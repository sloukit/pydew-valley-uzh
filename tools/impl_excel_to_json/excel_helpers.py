from typing import Optional

from openpyxl.worksheet.worksheet import Worksheet


def cell_value(sheet: Worksheet, cell_address: str) -> Optional[str]:
    """
    Returns the value of a cell, even if it's part of a merged range.

    Args:
        sheet (Worksheet): The worksheet object.
        cell_address (str): The address of the cell (e.g., "A2").

    Returns:
        Optional[str]: The value of the cell or the value of the master cell if it's part of a merged range.
    """
    cell = sheet[cell_address]

    # Check if the cell is part of a merged range
    for merged_range in sheet.merged_cells.ranges:
        if cell.coordinate in merged_range:
            master_cell = merged_range.start_cell  # Get the top-left (master) cell
            return sheet[
                master_cell.coordinate
            ].value  # Return the value of the master cell

    # If not merged, return the cell's own value
    return cell.value
