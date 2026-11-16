"""DuckDB handler for querying Parquet and JSON files."""
import duckdb
import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path


class DuckDBHandler:
    """Handle DuckDB connections and queries."""
    
    def __init__(self):
        """Initialize DuckDB handler."""
        self.conn = duckdb.connect(":memory:")
        self.loaded_files = {}
    
    def load_file(self, file_path: str, table_name: str) -> bool:
        """
        Load a Parquet or JSON file into DuckDB.
        
        Args:
            file_path: Path to the file
            table_name: Name of the table in DuckDB
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            # Drop table if it already exists
            try:
                self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            except:
                pass
            
            if file_ext == ".parquet":
                self.conn.execute(
                    f"CREATE TABLE {table_name} AS SELECT * FROM read_parquet('{file_path}')"
                )
            elif file_ext == ".json":
                self.conn.execute(
                    f"CREATE TABLE {table_name} AS SELECT * FROM read_json_auto('{file_path}')"
                )
            elif file_ext == ".csv":
                self.conn.execute(
                    f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{file_path}')"
                )
            else:
                return False
            
            self.loaded_files[table_name] = file_path
            return True
            
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def get_schema(self, table_name: str) -> Optional[pd.DataFrame]:
        """
        Get schema of a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            DataFrame with schema information
        """
        try:
            result = self.conn.execute(
                f"DESCRIBE {table_name}"
            ).fetchall()
            
            columns = ["Column", "Type", "Null", "Key", "Default", "Extra"]
            return pd.DataFrame(result, columns=columns)
        except Exception as e:
            print(f"Error getting schema: {e}")
            return None
    
    def execute_query(self, query: str) -> Optional[pd.DataFrame]:
        """
        Execute SQL query and return results as DataFrame.
        
        Args:
            query: SQL query string
            
        Returns:
            Query results as DataFrame
        """
        try:
            result = self.conn.execute(query).fetchall()
            
            # Get column names
            cursor = self.conn.execute(query)
            columns = [desc[0] for desc in cursor.description]
            
            df = pd.DataFrame(result, columns=columns)
            return df
            
        except Exception as e:
            print(f"Error executing query: {e}")
            return None
    
    def get_table_preview(self, table_name: str, limit: int = 5) -> Optional[pd.DataFrame]:
        """
        Get preview of table data.
        
        Args:
            table_name: Name of the table
            limit: Number of rows to return
            
        Returns:
            DataFrame with preview data
        """
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            return self.execute_query(query)
        except Exception as e:
            print(f"Error getting preview: {e}")
            return None
    
    def get_row_count(self, table_name: str) -> Optional[int]:
        """
        Get number of rows in table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Number of rows
        """
        try:
            result = self.conn.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting row count: {e}")
            return None
    
    def get_column_names(self, table_name: str) -> List[str]:
        """
        Get column names from table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column names
        """
        try:
            schema = self.get_schema(table_name)
            if schema is not None:
                return schema["Column"].tolist()
            return []
        except Exception as e:
            print(f"Error getting column names: {e}")
            return []
    
    def get_sample_data(self, table_name: str, limit: int = 10) -> Optional[Dict[str, Any]]:
        """
        Get sample data from table for context.
        
        Args:
            table_name: Name of the table
            limit: Number of rows
            
        Returns:
            Dictionary with sample data and metadata
        """
        try:
            preview = self.get_table_preview(table_name, limit)
            row_count = self.get_row_count(table_name)
            columns = self.get_column_names(table_name)
            
            return {
                "data": preview.to_dict(orient="records") if preview is not None else [],
                "row_count": row_count,
                "columns": columns,
                "column_count": len(columns)
            }
        except Exception as e:
            print(f"Error getting sample data: {e}")
            return None
    
    def get_data_dictionary(self, table_name: str) -> Optional[str]:
        """
        Generate a data dictionary describing columns and their values.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Formatted data dictionary string
        """
        try:
            schema = self.get_schema(table_name)
            if schema is None:
                return None
            
            preview = self.get_table_preview(table_name, 100)
            if preview is None:
                return None
            
            dictionary = "DATA DICTIONARY:\n\n"
            
            for col in preview.columns:
                col_data = preview[col]
                col_type = str(col_data.dtype)
                
                dictionary += f"Column: {col}\n"
                dictionary += f"  Type: {col_type}\n"
                dictionary += f"  Sample values: {col_data.dropna().unique()[:5].tolist()}\n"
                dictionary += f"  Non-null count: {col_data.notna().sum()}/{len(col_data)}\n\n"
            
            return dictionary
        except Exception as e:
            print(f"Error generating data dictionary: {e}")
            return None
    
    def close(self):
        """Close DuckDB connection."""
        if self.conn:
            self.conn.close()
