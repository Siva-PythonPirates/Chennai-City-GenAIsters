from typing import List, Optional
from datetime import datetime
from modals import Receipt, ReceiptItemData


def add_reciept_data(
    user_id: str,
    vendor: str,
    total: str,
    tax: float,
    date: Optional[datetime],
    item_names: List[str],
    item_costs: List[float],
    item_quantities: List[int],
    additional_items_data: Optional[str] = "{}",
    additional_data: Optional[str] = "{}",
) -> str:
    """
    Adds the new receipt to the database for a user.
    Args:
        user_id (str): The ID of the user.
        vendor (str): The vendor of the receipt, if not provided, it will be set to "Unknown".
        total (str): The total amount of the receipt.
        tax (float): The tax amount of the receipt, if no tax set to 0
        date (Optional[datetime]): The date of the receipt.
        item_names (List[ReceiptItem]): List of items in the receipt.
        item_costs (List[float]): List of costs for each item.
        item_quantities (List[int]): List of quantities for each item.
        additional_items_data (Optional[str]): Additional data for the items, default is "{}".
        additional_data (Optional[str]): Additional data for the receipt, default is "{}".
    Returns:
        str: The ID of the created receipt.
    """
    return


def delete_reciept_data(user_id: str, receipt_id: str) -> bool:
    """
    Deletes a receipt for a user.
    Args:
        user_id (str): The ID of the user.
        receipt_id (str): The ID of the receipt to be deleted.
    Returns:
        bool: True if the receipt was deleted successfully, False otherwise.
    """
    return
