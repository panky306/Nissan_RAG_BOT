"""OpenAI LLM handler for RAG chatbot."""
from openai import OpenAI
from typing import Optional, List, Dict, Any


class LLMHandler:
    """Handle OpenAI API interactions."""
    
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
            Generated SQL query
        """
        prompt = f"""You are a SQL expert who understands business terminology.

CRITICAL CONSTRAINTS - YOU MUST FOLLOW THESE:
1. ONLY use columns that exist in the provided schema
2. ONLY query data that is explicitly in the table
3. DO NOT make assumptions about data that doesn't exist
4. DO NOT generate queries for columns not listed in schema
5. If the user asks about something not in the schema, respond with: "COLUMN_NOT_FOUND"
6. If you cannot map the question to available columns, respond with: "UNMAPPABLE_QUESTION"

The schema includes business column explanations. Use these to understand 
what the user is asking for, even if they use business terms instead of technical column names.

For example:
- User asks about "dealer" or "dealership" → use column 'dlr_nb' (if it exists)
- User asks about "vehicle model" or "model" → use column 'mdl_ln_cd' (if it exists)
- User asks about "predicted demand" or "forecast" → use column 'forecast' (if it exists)
- User asks about "actual sales" or "observed demand" → use column 'actual' (if it exists)
- User asks about "data quality" → check 'thin_history' column (if it exists)

Generate a SQL query to answer the following business question.

Table name: {table_name}

Table schema with business context:
{schema_info}

Business Question: {question}

Generate only the SQL query, without any explanation or markdown formatting.
Return just the query that can be directly executed.
Ensure the query:
1. Uses ONLY columns listed in the schema above
2. Does NOT assume data or columns that don't exist
3. Handles business logic appropriately
4. Will produce meaningful results for the business question

If ANY column in your query is not in the schema, respond with: COLUMN_NOT_FOUND"""
        
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
