"""Data dictionary for common AWS ML and business data."""

# Dictionary mapping column names to their meanings
COLUMN_DESCRIPTIONS = {
    # AWS ML Model Data
    "dlr_nb": {
        "description": "Dealer Number - identifies which Nissan dealership",
        "example": "01016",
        "data_type": "string"
    },
    "mdl_ln_cd": {
        "description": "Model Line Code - vehicle model identifier",
        "example": "720 (Altima), ALT (Altima Variant), ARI (Ariya EV)",
        "data_type": "string"
    },
    "full_mdl_yr_3_cd": {
        "description": "Model Year Code - vehicle production year",
        "example": "240 (2024), 250 (2025), 260 (2026), 270 (2027)",
        "data_type": "string"
    },
    "trm_cd": {
        "description": "Trim Code - vehicle trim/package level",
        "example": "G (Base), X (Premium), K (Special), Y (Optional), N (Entry)",
        "data_type": "string"
    },
    "drv_trn_cd": {
        "description": "Drivetrain Code - transmission and wheel drive type",
        "example": "4WD (4-wheel), 2WD (2-wheel), AWD (All-wheel), FWD (Front-wheel)",
        "data_type": "string"
    },
    "forecast": {
        "description": "ML Model Forecast - predicted demand/units to sell",
        "example": "0.0014 (very low demand), 3.9557 (high demand)",
        "data_type": "decimal",
        "range": "0.0 to 10.0+"
    },
    "actual": {
        "description": "Actual - real observed demand/units sold",
        "example": "0 (no sales), 4 (4 units sold)",
        "data_type": "decimal",
        "range": "0.0 to 10.0+"
    },
    "thin_history": {
        "description": "Data Quality Flag - indicates if model has sufficient historical data",
        "example": "0 (good data - model confident), 1 (sparse data - less confident)",
        "data_type": "integer"
    },
    "reason": {
        "description": "Explanation - reason for discrepancy between forecast and actual",
        "example": "Usually empty, populated when prediction significantly misses actual",
        "data_type": "string"
    },
    "run_id": {
        "description": "Model Run ID - which model execution generated this prediction",
        "example": "2ee152bd11de",
        "data_type": "string"
    },
    "created_at": {
        "description": "Timestamp - when the prediction was generated",
        "example": "2026-11-13T10:25:12Z",
        "data_type": "timestamp"
    },
}

# Common business metrics and their calculations
BUSINESS_METRICS = {
    "forecast_accuracy": {
        "description": "How accurate the ML model's predictions were",
        "calculation": "ABS(forecast - actual) / actual",
        "good_range": "< 0.2 (less than 20% error)"
    },
    "demand_level": {
        "description": "Classification of demand volume",
        "categories": {
            "very_low": "0.0 - 0.05 (niche configurations)",
            "low": "0.05 - 0.3 (occasional sales)",
            "moderate": "0.3 - 1.0 (regular sales)",
            "high": "1.0 - 3.0 (popular configurations)",
            "very_high": "3.0+ (best sellers)"
        }
    },
    "model_confidence": {
        "description": "How confident the model is in its prediction",
        "based_on": "thin_history flag (0=confident, 1=uncertain)"
    }
}

# Common questions and their interpretations
COMMON_QUESTIONS = {
    "How many products?": "Count total rows in dataset",
    "What's the average forecast?": "Average of forecast column",
    "Which has highest demand?": "Row with maximum forecast value",
    "Products with forecast > X?": "Filter by forecast value",
    "Forecast accuracy?": "Compare forecast vs actual values",
    "How many thin_history=1?": "Data quality assessment",
    "By model analysis?": "Group by mdl_ln_cd",
    "By year analysis?": "Group by full_mdl_yr_3_cd",
    "Best predictions?": "Where forecast close to actual",
    "Worst predictions?": "Where forecast differs from actual",
}


def get_column_explanation(column_name: str) -> str:
    """Get explanation for a specific column."""
    if column_name in COLUMN_DESCRIPTIONS:
        info = COLUMN_DESCRIPTIONS[column_name]
        return f"Column '{column_name}': {info['description']} (Example: {info['example']})"
    return f"No explanation available for column '{column_name}'"


def get_full_data_dictionary() -> str:
    """Get complete data dictionary as formatted text."""
    text = "=" * 80 + "\n"
    text += "DATA DICTIONARY - COLUMN MEANINGS\n"
    text += "=" * 80 + "\n\n"
    
    for col_name, info in COLUMN_DESCRIPTIONS.items():
        text += f"{col_name}:\n"
        text += f"  Description: {info['description']}\n"
        text += f"  Type: {info.get('data_type', 'unknown')}\n"
        text += f"  Example: {info['example']}\n"
        if 'range' in info:
            text += f"  Range: {info['range']}\n"
        text += "\n"
    
    return text


def get_business_context() -> str:
    """Get business context for the data."""
    text = "BUSINESS CONTEXT:\n"
    text += "-" * 60 + "\n"
    text += "This is vehicle demand forecasting data from an AWS ML model.\n\n"
    text += "PURPOSE: Predict which vehicle configurations will sell at each dealership\n"
    text += "to optimize inventory allocation and production planning.\n\n"
    text += "KEY INSIGHT:\n"
    text += "- 'forecast' = What ML model predicts will sell\n"
    text += "- 'actual' = What actually sold\n"
    text += "- 'thin_history' = Whether we have good data (0=yes, 1=no)\n\n"
    text += "EXAMPLE INTERPRETATION:\n"
    text += "If forecast=3.9557 and actual=4, the model was 99% accurate.\n"
    text += "Stock this configuration heavily.\n\n"
    text += "If forecast=2.2307, actual=0.6667, and thin_history=1,\n"
    text += "the model had limited data and overpredicted. Be cautious.\n"
    
    return text
