"""Test cases for SQL column validation."""
import pytest
from src.llm_handler import validate_sql_columns, LLMHandler


# Available columns for testing
AVAILABLE_COLUMNS = {
    'actual', 'created_at', 'dlr_nb', 'drv_trn_cd', 'forecast',
    'full_mdl_yr_3_cd', 'mdl_ln_cd', 'reason', 'run_id', 'thin_history', 'trm_cd'
}


class TestInvalidColumnDetection:
    """Tests for detecting invalid column references in SQL."""
    
    def test_invalid_column_total_forecast(self):
        """Test detection of invalid 'total_forecast' column."""
        sql = "SELECT mdl_ln_cd, total_forecast FROM data"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == False, "Should detect invalid 'total_forecast' column"
        assert "total_forecast" in result["invalid_columns"]
        assert "Available columns" in result["error_message"]
    
    def test_invalid_column_year(self):
        """Test detection of invalid 'year' column."""
        sql = "SELECT year FROM data"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == False, "Should detect invalid 'year' column"
        assert "year" in result["invalid_columns"]
    
    def test_invalid_column_profit(self):
        """Test detection of invalid 'profit' column."""
        sql = "SELECT * FROM data WHERE profit > 0"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == False, "Should detect invalid 'profit' column"
        assert "profit" in result["invalid_columns"]
    
    def test_invalid_column_revenue(self):
        """Test detection of invalid 'revenue' column."""
        sql = "SELECT revenue FROM data WHERE dlr_nb = 5"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == False, "Should detect invalid 'revenue' column"
        assert "revenue" in result["invalid_columns"]
    
    def test_multiple_invalid_columns(self):
        """Test detection of multiple invalid columns."""
        sql = "SELECT mdl_ln_cd, total_forecast, profit, revenue FROM data"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == False
        invalid_set = set(result["invalid_columns"])
        assert "total_forecast" in invalid_set
        assert "profit" in invalid_set
        assert "revenue" in invalid_set
    
    def test_error_message_format(self):
        """Test that error message contains helpful information."""
        sql = "SELECT invalid_col FROM data"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        error_msg = result["error_message"]
        assert "invalid_col" in error_msg, "Should mention the invalid column"
        assert "Available columns" in error_msg, "Should list available columns"


class TestValidQueryPass:
    """Tests for valid queries that should pass validation."""
    
    def test_valid_query_all_columns(self):
        """Test that wildcard SELECT passes."""
        sql = "SELECT * FROM data"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == True, "Wildcard SELECT should pass"
        assert len(result["invalid_columns"]) == 0
        assert result["error_message"] is None
    
    def test_valid_query_specific_columns(self):
        """Test that query with specific available columns passes."""
        sql = "SELECT mdl_ln_cd, forecast, actual FROM data"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == True
        assert len(result["invalid_columns"]) == 0
    
    def test_valid_query_with_aggregation(self):
        """Test that aggregation with available columns passes."""
        sql = "SELECT mdl_ln_cd, SUM(forecast) as total_forecast FROM data GROUP BY mdl_ln_cd"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == True, "Aggregation with valid columns should pass"
        assert len(result["invalid_columns"]) == 0
    
    def test_valid_query_with_where_clause(self):
        """Test that WHERE clause with available columns passes."""
        sql = "SELECT * FROM data WHERE actual > forecast"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == True
        assert len(result["invalid_columns"]) == 0
    
    def test_valid_query_with_order_by(self):
        """Test that ORDER BY with available columns passes."""
        sql = "SELECT mdl_ln_cd, forecast FROM data ORDER BY forecast DESC LIMIT 3"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == True
        assert len(result["invalid_columns"]) == 0
    
    def test_valid_query_with_group_by(self):
        """Test that GROUP BY with available columns passes."""
        sql = "SELECT dlr_nb, AVG(forecast) FROM data GROUP BY dlr_nb"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == True
        assert len(result["invalid_columns"]) == 0
    
    def test_valid_query_with_distinct(self):
        """Test that DISTINCT with available columns passes."""
        sql = "SELECT DISTINCT mdl_ln_cd FROM data"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == True
        assert len(result["invalid_columns"]) == 0
    
    def test_valid_query_with_count(self):
        """Test that COUNT with available columns passes."""
        sql = "SELECT COUNT(*) FROM data WHERE thin_history = 0"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == True
        assert len(result["invalid_columns"]) == 0
    
    def test_valid_query_with_date_filter(self):
        """Test that date filtering with available columns passes."""
        sql = "SELECT * FROM data WHERE created_at > '2026-01-01'"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == True
        assert len(result["invalid_columns"]) == 0
    
    def test_valid_query_top_3_models(self):
        """Test the specific query that was failing: 'top 3 models ordered by forecast'."""
        sql = "SELECT mdl_ln_cd, forecast FROM data ORDER BY forecast DESC LIMIT 3"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == True, "Query for top 3 models should pass"
        assert len(result["invalid_columns"]) == 0


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""
    
    def test_empty_sql_string(self):
        """Test that empty SQL string is handled gracefully."""
        sql = ""
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == False
        assert "empty" in result["error_message"].lower()
    
    def test_sql_with_string_literals(self):
        """Test that string literals don't cause false positives."""
        sql = "SELECT * FROM data WHERE reason LIKE '%profit%'"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == True, "String literals should not cause false positives"
        assert "profit" not in result["invalid_columns"]
    
    def test_sql_case_insensitivity(self):
        """Test that SQL keyword case doesn't matter."""
        sql = "select mdl_ln_cd, forecast from data where actual > forecast"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == True
        assert len(result["invalid_columns"]) == 0
    
    def test_sql_with_numeric_literals(self):
        """Test that numeric literals don't cause false positives."""
        sql = "SELECT * FROM data WHERE dlr_nb = 12345 AND forecast > 3.14"
        result = validate_sql_columns(sql, AVAILABLE_COLUMNS)
        assert result["is_valid"] == True
        # Numbers like 12345 and 3.14 should not be treated as column names
        assert "12345" not in result["invalid_columns"]
        assert "3" not in result["invalid_columns"]


class TestLLMHandlerValidation:
    """Tests for LLMHandler's use of validate_sql_columns."""
    
    def test_llm_handler_available_columns(self):
        """Test that LLMHandler has correct available columns."""
        assert LLMHandler.AVAILABLE_COLUMNS == AVAILABLE_COLUMNS
    
    def test_llm_handler_available_columns_count(self):
        """Test that exactly 11 columns are available."""
        assert len(LLMHandler.AVAILABLE_COLUMNS) == 11, "Should have exactly 11 available columns"
    
    def test_llm_handler_available_columns_content(self):
        """Test that all required columns are present."""
        required_columns = {
            'actual', 'created_at', 'dlr_nb', 'drv_trn_cd', 'forecast',
            'full_mdl_yr_3_cd', 'mdl_ln_cd', 'reason', 'run_id', 'thin_history', 'trm_cd'
        }
        assert LLMHandler.AVAILABLE_COLUMNS == required_columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
