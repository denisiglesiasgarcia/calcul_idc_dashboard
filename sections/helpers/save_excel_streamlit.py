# sections/helpers/save_excel_streamlit.py

import logging
from datetime import datetime
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd
from openpyxl.utils import get_column_letter

# Configure logging with timestamp
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ExcelExportError(Exception):
    """Custom exception for Excel export errors with detailed messaging"""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


def validate_data(data: pd.DataFrame | dict[str, Any]) -> pd.DataFrame:
    """
    Validate and convert input data to DataFrame with comprehensive error checking.

    Args:
        data: Input data (DataFrame or dictionary)

    Returns:
        pd.DataFrame: Validated and processed DataFrame

    Raises:
        ExcelExportError: If validation fails
    """
    try:
        # Check for None or empty input
        if data is None:
            raise ExcelExportError("Input data cannot be None")

        if isinstance(data, dict) and not data:
            raise ExcelExportError("Input dictionary is empty")

        if isinstance(data, dict):
            # Process dictionary items with type checking
            processed_items = []
            for k, v in data.items():
                # Validate key
                if not isinstance(k, (str, int, float)):
                    k = str(k)

                # Process value based on type
                if v is None:
                    processed_value = ""
                elif isinstance(v, (dict, list)):
                    processed_value = str(v)
                elif isinstance(v, (datetime, pd.Timestamp)):
                    processed_value = v.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(v, (int, float)):
                    processed_value = v
                elif isinstance(v, bool):
                    processed_value = str(v)
                else:
                    processed_value = str(v)

                processed_items.append({"Key": k, "Value": processed_value})

            df = pd.DataFrame(processed_items)

        elif isinstance(data, pd.DataFrame):
            # Handle missing values consistently
            df = data.replace({np.nan: "", None: "", "nan": "", "None": "", "NaT": ""})

            # Convert any remaining problematic types
            for col in df.columns:
                if df[col].dtype == "object":
                    df[col] = df[col].apply(lambda x: str(x) if x != "" else "")

        else:
            raise ExcelExportError(
                f"Unsupported data type: {type(data)}. Expected DataFrame or dictionary."
            )

        # Final validation
        if df.empty:
            raise ExcelExportError("Resulting DataFrame is empty")

        # Validate column names
        df.columns = [str(col) for col in df.columns]

        return df

    except ExcelExportError:
        raise
    except Exception as e:
        raise ExcelExportError(
            f"Data validation failed: {str(e)}", original_error=e
        ) from e


def convert_df_to_excel(data: pd.DataFrame | dict[str, Any]) -> bytes:
    """
    Convert data to Excel bytes with enhanced error handling and formatting.

    Args:
        data: Input data (DataFrame or dictionary)

    Returns:
        bytes: Excel file as bytes

    Raises:
        ExcelExportError: If conversion fails
    """
    output = None
    try:
        # Validate and process input data
        df = validate_data(data)

        # Create Excel file in memory
        output = BytesIO()

        # Write to Excel with formatting
        with pd.ExcelWriter(output, engine="openpyxl", mode="wb") as writer:
            # Write DataFrame
            df.to_excel(writer, index=False, sheet_name="Sheet1", float_format="%.2f")

            # Get worksheet
            worksheet = writer.sheets["Sheet1"]

            # Format columns
            for idx, col in enumerate(df.columns):
                column = df[col]
                # Calculate max length considering header and content
                max_length = max(
                    max(column.astype(str).str.len().max(), len(str(col)))
                    + 2,  # Add padding
                    5,  # Minimum width
                )
                # Cap maximum width
                max_length = min(max_length, 50)

                # Set column width
                worksheet.column_dimensions[
                    get_column_letter(idx + 1)
                ].width = max_length

            # Style header row
            for cell in worksheet[1]:
                cell.style = "Headline 3"

        # Get Excel data
        excel_data = output.getvalue()

        # Verify output
        if not excel_data:
            raise ExcelExportError("Generated Excel file is empty")

        return excel_data

    except ExcelExportError:
        raise
    except Exception as e:
        raise ExcelExportError(
            f"Excel conversion failed: {str(e)}", original_error=e
        ) from e
    finally:
        if output:
            output.close()
