"""RAG pipeline orchestration."""
import re
from typing import Optional, Dict, Any, Tuple
from .duckdb_handler import DuckDBHandler
from .llm_handler import LLMHandler
from .data_dictionary import get_full_data_dictionary, get_business_context


class RAGPipeline:
    """Orchestrate RAG (Retrieval-Augmented Generation) pipeline."""
    
    def __init__(self, llm_handler: LLMHandler):
        """
        Initialize RAG pipeline.
        
        Args:
            llm_handler: LLM handler instance
        """
        self.duckdb = DuckDBHandler()
        self.llm = llm_handler
        self.current_table = None
    
    def load_data(self, file_path: str, table_name: str = "data") -> bool:
        """
        Load data file.
        
        Args:
            file_path: Path to data file
            table_name: Name for the table
            
        Returns:
            True if successful
        """
        success = self.duckdb.load_file(file_path, table_name)
        if success:
            self.current_table = table_name
        return success
    
    def process_question(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Process a question through the RAG pipeline.
        
        Args:
            question: Natural language question
            
        Returns:
            Dictionary with query, results, and answer
        """
        if not self.current_table:
            return {
                "error": "No data loaded. Please upload a file first."
            }
        
        try:
            # Step 1: Get schema information
            schema = self.duckdb.get_schema(self.current_table)
            sample_data = self.duckdb.get_sample_data(self.current_table, limit=3)
            
            if schema is None:
                return {"error": "Failed to get table schema"}
            
            # Format schema for LLM
            schema_str = schema.to_string()
            sample_str = str(sample_data) if sample_data else ""
            
            # ENHANCED: Add data dictionary context if available
            context_info = self._get_column_context(sample_data.get("columns", []) if sample_data else [])
            
            full_context = f"""
{schema_str}

Sample data:
{sample_str}

{context_info}
"""
            
            # Step 2: Generate SQL query
            sql_query = self.llm.generate_sql_query(
                question, 
                full_context,
                self.current_table
            )
            
            if not sql_query:
                return {
                    "error": "Unable to map your question to available data columns. "
                             "Please check that the information you're asking about exists in your dataset."
                }
            
            # ANTI-HALLUCINATION: Validate generated SQL uses only available columns
            available_columns = set(self.duckdb.get_column_names(self.current_table))
            sql_upper = sql_query.upper()
            
            # Extract column names from SQL (simplified check)
            import re
            # Look for column references like WHERE col = or SELECT col
            potential_cols = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', sql_query)
            
            sql_keywords = {'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'ORDER', 'BY', 'GROUP', 
                           'HAVING', 'LIMIT', 'AS', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 
                           'ROUND', 'ABS', 'NULL', 'NOT', 'IN', 'LIKE', 'BETWEEN', 'CASE', 
                           'WHEN', 'THEN', 'ELSE', 'END', 'DISTINCT', 'DESC', 'ASC', 'JOIN',
                           'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'CROSS', 'UNION', 'ALL'}
            
            unrecognized_cols = [col for col in potential_cols 
                                if col.upper() not in sql_keywords 
                                and col not in available_columns]
            
            if unrecognized_cols:
                return {
                    "error": f"Generated query references unavailable columns: {', '.join(set(unrecognized_cols))}. "
                             f"These columns do not exist in your dataset. "
                             f"Available columns: {', '.join(sorted(available_columns))}"
                }
            
            # Step 3: Execute query
            query_result = self.duckdb.execute_query(sql_query)
            
            if query_result is None:
                return {
                    "error": "Failed to execute query. Please check your data.",
                    "sql_query": sql_query
                }
            
            # ANTI-HALLUCINATION: Check if results are empty
            if len(query_result) == 0:
                return {
                    "question": question,
                    "sql_query": sql_query,
                    "query_results": query_result,
                    "answer": "No data matches your query criteria. The dataset does not contain records that satisfy your question.",
                    "row_count": 0
                }
            
            # Step 4: Generate answer
            result_str = query_result.to_string()
            answer = self.llm.generate_answer(question, result_str, context_info)
            
            if not answer:
                answer = f"Query returned {len(query_result)} results. Unable to generate summary."
            
            return {
                "question": question,
                "sql_query": sql_query,
                "query_results": query_result,
                "answer": answer,
                "row_count": len(query_result)
            }
            
        except Exception as e:
            return {
                "error": f"Error processing question: {str(e)}"
            }
    
    def _get_column_context(self, columns: list) -> str:
        """
        Get business context for columns in the data.
        
        Args:
            columns: List of column names
            
        Returns:
            Formatted context string for LLM
        """
        from .data_dictionary import COLUMN_DESCRIPTIONS
        
        context = "\nCOLUMN MEANINGS:\n"
        for col in columns:
            if col in COLUMN_DESCRIPTIONS:
                info = COLUMN_DESCRIPTIONS[col]
                context += f"  {col}: {info['description']}\n"
        
        # Add business context if this looks like AWS ML data
        if any(col in columns for col in ['forecast', 'actual', 'thin_history']):
            context += "\n" + get_business_context()
        
        return context
    
    def get_table_info(self) -> Optional[Dict[str, Any]]:
        """Get information about loaded table."""
        if not self.current_table:
            return None
        
        return {
            "table_name": self.current_table,
            "schema": self.duckdb.get_schema(self.current_table),
            "row_count": self.duckdb.get_row_count(self.current_table),
            "column_names": self.duckdb.get_column_names(self.current_table),
            "sample_data": self.duckdb.get_table_preview(self.current_table, limit=5)
        }
    
    def close(self):
        """Close pipeline connections."""
        self.duckdb.close()
