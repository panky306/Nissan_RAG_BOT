"""OpenAI LLM handler for RAG chatbot."""
from openai import OpenAI
from typing import Optional, List, Dict, Any
import re


# SQL keywords that should be filtered out during column validation
SQL_KEYWORDS = {
    'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT',
    'AS', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'ROUND', 'ABS', 'NULL', 'NOT', 'IN',
    'LIKE', 'BETWEEN', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'DISTINCT', 'DESC', 'ASC',
    'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'CROSS', 'UNION', 'ALL',
    'DATA'  # Common generic table name
}


def validate_sql_columns(sql: str, available_columns: set) -> Dict[str, Any]:
    """
    Validate that SQL query only references available columns.
    
    Args:
        sql: SQL query string to validate
        available_columns: Set of allowed column names
        
    Returns:
        {
            "is_valid": bool,
            "invalid_columns": list of unrecognized column references,
            "error_message": str or None
        }
    """
    if not sql:
        return {
            "is_valid": False,
            "invalid_columns": [],
            "error_message": "SQL query is empty"
        }
    
    # Extract all identifiers from SQL using regex: \b([a-zA-Z_][a-zA-Z0-9_]*)\b
    identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', sql)
    
    # Filter out SQL keywords and function names (case-insensitive)
    potential_columns = [
        identifier for identifier in identifiers
        if identifier.upper() not in SQL_KEYWORDS
    ]
    
    # Find invalid column references
    invalid_columns = [
        col for col in potential_columns
        if col not in available_columns
    ]
    
    # Remove duplicates while preserving order
    invalid_columns = list(dict.fromkeys(invalid_columns))
    
    if invalid_columns:
        error_message = (
            f"Generated query references invalid columns: {', '.join(invalid_columns)}. "
            f"These columns do not exist in your dataset. "
            f"Available columns: {', '.join(sorted(available_columns))}"
        )
        return {
            "is_valid": False,
            "invalid_columns": invalid_columns,
            "error_message": error_message
        }
    
    return {
        "is_valid": True,
        "invalid_columns": [],
        "error_message": None
    }


class LLMHandler:
    """Handle OpenAI API interactions."""
    
    # Available columns in the dataset (exactly 11 columns)
    AVAILABLE_COLUMNS = {
        'actual', 'created_at', 'dlr_nb', 'drv_trn_cd', 'forecast',
        'full_mdl_yr_3_cd', 'mdl_ln_cd', 'reason', 'run_id', 'thin_history', 'trm_cd'
    }
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize LLM handler.
        
        Args:
            api_key: OpenAI API key
            model: Model name to use
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def generate_sql_query(self, question: str, schema_info: str, table_name: str) -> Optional[str]:
        """
        Generate SQL query from natural language question.
        
        Args:
            question: Natural language question
            schema_info: Table schema information with business context
            table_name: Name of the table to query
            
        Returns:
            Generated SQL query, or None if validation fails or error occurs
        """
        prompt = f"""You are a SQL expert. Generate VALID SQL queries ONLY using columns that exist in the schema.

CRITICAL RULES:
1. ONLY use columns that exist in the provided schema - NO EXCEPTIONS
2. When user says "total X", use SUM(column_name) 
3. When user says "average X", use AVG(column_name)
4. When user says "top 3" or "top N", use ORDER BY column DESC LIMIT N
5. When user says "by model" or "by category", use GROUP BY column_name
6. DO NOT create columns that don't exist (e.g., total_forecast, year, data)
7. If a column doesn't exist, respond with: COLUMN_NOT_FOUND
8. If you cannot map the question to available columns, respond with: UNMAPPABLE_QUESTION

AVAILABLE COLUMNS (ONLY use these exact names):
- actual
- created_at
- dlr_nb
- drv_trn_cd
- forecast
- full_mdl_yr_3_cd
- mdl_ln_cd
- reason
- run_id
- thin_history
- trm_cd

DO NOT create, derive, or reference any columns not in this list.
DO NOT use generic table names like 'data' - use the exact table name provided.
DO NOT create column aliases that reference non-existent columns.

Column Name Mappings:
- "model" or "model line" or "vehicle model" → mdl_ln_cd
- "forecast" or "predicted" or "prediction" → forecast
- "actual" or "real sales" or "observed" → actual
- "dealer" or "dealership" → dlr_nb
- "trim" → trm_cd
- "drivetrain" or "drive type" → drv_trn_cd
- "quality" or "data quality" → thin_history
- "year" or "model year" → full_mdl_yr_3_cd
- "date" or "created" or "timestamp" → created_at

EXAMPLE TRANSFORMATIONS:
- User: "Top 3 models by forecast" 
  SQL: SELECT mdl_ln_cd, forecast FROM {table_name} ORDER BY forecast DESC LIMIT 3

- User: "Average forecast by dealer"
  SQL: SELECT dlr_nb, AVG(forecast) as avg_forecast FROM {table_name} GROUP BY dlr_nb ORDER BY avg_forecast DESC

- User: "Configurations with actual > forecast"
  SQL: SELECT * FROM {table_name} WHERE actual > forecast LIMIT 100

Generate a SQL query to answer: {question}

Table name: {table_name}

Schema and sample data:
{schema_info}

RESPONSE: Generate ONLY the SQL query. No explanation. No markdown. Just the query.
If any column in your query is not in the available columns list, respond with: COLUMN_NOT_FOUND"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_completion_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            query = response.choices[0].message.content.strip()
            
            # Check for error indicators
            if "COLUMN_NOT_FOUND" in query or "UNMAPPABLE_QUESTION" in query:
                return None
            
            # Remove markdown code blocks if present
            if query.startswith("```"):
                query = query.split("```")[1]
                if query.startswith("sql"):
                    query = query[3:]
                query = query.strip()
            
            # VALIDATION: Check that generated SQL only uses available columns
            validation = validate_sql_columns(query, self.AVAILABLE_COLUMNS)
            if not validation["is_valid"]:
                print(f"SQL Validation Failed: {validation['error_message']}")
                return None
            
            return query
            
        except Exception as e:
            print(f"Error generating SQL query: {e}")
            return None
    
    def generate_answer(self, question: str, query_result: str, context: str = "") -> Optional[str]:
        """
        Generate natural language answer from query results.
        
        Args:
            question: Original question
            query_result: Results from SQL query
            context: Additional context (includes column meanings)
            
        Returns:
            Natural language answer using business terminology
        """
        prompt = f"""You are a helpful business analyst. Answer the following question based STRICTLY on the provided data.

🚨 CRITICAL ANTI-HALLUCINATION RULES 🚨
1. ONLY answer based on the data provided in "Data retrieved from database"
2. DO NOT make up or assume any data
3. DO NOT extrapolate beyond what's in the results
4. DO NOT provide information not explicitly in the query results
5. If the data doesn't answer the question, say: "The available data does not contain information to answer this question."
6. Do NOT reference data that isn't shown in the results
7. ALWAYS cite the specific values from the data
8. If results are empty or insufficient, clearly state that

Question: {question}

Data retrieved from database:
{query_result}

{f'Business Context & Column Meanings: {context}' if context else ''}

RESPONSE GUIDELINES:
1. Use business language, NOT technical column names
2. Instead of "dlr_nb", say "Dealer" or "Dealership"
3. Instead of "mdl_ln_cd", say "Model" or "Vehicle Model"
4. Instead of "forecast", say "Predicted Demand" or "Model Forecast"
5. Instead of "actual", say "Actual Sales" or "Observed Demand"
6. Instead of "thin_history=1", say "Limited Historical Data"
7. Instead of "thin_history=0", say "Reliable Historical Data"
8. Round numbers to 2 decimal places for readability
9. ONLY provide insights based on the actual data returned
10. CITE specific values from the results

CRITICAL: If the question asks for information not present in the results, 
clearly state "This information is not available in the current dataset."

Example of CORRECT response:
- User asks: "Which model has the highest forecast?"
- Data shows: mdl_ln_cd=720, forecast=3.9557
- Correct answer: "Based on the data retrieved, the Altima sedan (model 720) shows the highest 
  predicted demand with a forecast value of 3.96 units."

Example of WRONG response (hallucination):
- User asks: "Which model is most profitable?"
- Data shows: mdl_ln_cd=720, forecast=3.9557, actual=4
- WRONG: "The Altima is most profitable because it has high demand." ← NOT IN DATA
- RIGHT: "The Altima shows high predicted demand (3.96 units) and actual sales of 4 units. 
  Profitability information is not available in the current dataset."

Provide a clear, concise answer based ONLY on the provided data."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_completion_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, str]:
        """Get information about current model."""
        return {
            "model": self.model,
            "provider": "OpenAI"
        }
