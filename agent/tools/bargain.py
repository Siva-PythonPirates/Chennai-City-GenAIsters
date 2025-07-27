import json
import requests
from typing import Literal
from google.cloud import firestore
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from utility.config import configurations

db = firestore.Client("agenticai")


def get_balance(user_id: str) -> float:
    """
    this function is used to retrieve the balance for a user
    Args:
        user_id (str): The ID of the user.
    Returns:
        float: The balance of the user.
    """
    try:
        users_ref = db.collection("users")
        query = users_ref.where("user_id", "==", user_id).limit(1).stream()
        balance = 0.0
        for doc in query:
            balance = doc.to_dict().get("balance", 0.0)
            break
        return balance
    except Exception as e:
        print("hhh")
        return 0.0


def send_money(sender_id: str, receiver_id: str, amount: float) -> bool:
    """
    This function sends money from sender to receiver.
    Args:
        sender_id (str): The ID of the sender user.
        receiver_id (str): The ID of the recipient user.
        amount (float): The amount to send.
    Returns:
        bool: True if the transaction was successful, False otherwise.
    """
    try:
        users_ref = db.collection("users")
        sender_query = users_ref.where("user_id", "==", sender_id).limit(1).stream()
        receiver_query = users_ref.where("user_id", "==", receiver_id).limit(1).stream()

        sender_doc = next(sender_query, None)
        receiver_doc = next(receiver_query, None)

        if sender_doc is None or receiver_doc is None:
            return False

        sender_data = sender_doc.to_dict()
        receiver_data = receiver_doc.to_dict()

        if sender_data.get("balance", 0.0) < amount:
            return False

        # Update balances
        users_ref.document(sender_doc.id).update(
            {"balance": sender_data["balance"] - amount}
        )
        users_ref.document(receiver_doc.id).update(
            {"balance": receiver_data["balance"] + amount}
        )

        return True
    except Exception as e:
        return False


def get_money(sender_id: str, user_id: str, amount: float):
    """
    This function allows a user to receive money from a sender.
    Args:
        sender_id (str): The ID of the sender user.
        user_id (str): The ID of the recipient user.
        amount (float): The amount to receive.
    Returns:
        bool: True if the transaction was successful, False otherwise.
    """
    try:
        users_ref = db.collection("users")
        sender_query = users_ref.where("user_id", "==", sender_id).limit(1).stream()
        receiver_query = users_ref.where("user_id", "==", user_id).limit(1).stream()

        sender_doc = next(sender_query, None)
        receiver_doc = next(receiver_query, None)

        if sender_doc is None or receiver_doc is None:
            return False

        sender_data = sender_doc.to_dict()
        receiver_data = receiver_doc.to_dict()

        if sender_data.get("balance", 0.0) < amount:
            return False

        # Update balances
        users_ref.document(sender_doc.id).update(
            {"balance": sender_data["balance"] - amount}
        )
        users_ref.document(receiver_doc.id).update(
            {"balance": receiver_data["balance"] + amount}
        )

        return True
    except Exception as e:
        return False


def get_inventory(user_id: str, items: list, quantity: int):
    """
    This function retrieves inventory items for a user.
    Args:
        user_id (str): The ID of the user.
        items (list): List of item names to retrieve.
        quantity (int): Minimum quantity to filter items.
    Returns:
        list: List of inventory items matching criteria.
    """
    try:
        inventory_ref = db.collection("inventory")
        query = inventory_ref.where("user_id", "==", user_id).stream()
        result = []
        for doc in query:
            data = doc.to_dict()
            if data.get("item") in items and data.get("quantity", 0) >= quantity:
                result.append(data)
        return result
    except Exception as e:
        return []


def add_inventory(
    user_id: str, cost: int, quantity: int, product_id: str, product: str
):
    """
    This function adds a new inventory item for a user.
    Args:
        user_id (str): The ID of the user.
        cost (int): The cost of the item.
        quantity (int): The quantity of the item.
        product_id (str): The product ID.
        product (str): The name of the product.
    Returns:
        bool: True if the item was added successfully, False otherwise.
    """
    try:
        inventory_ref = db.collection("inventory")
        new_item = {
            "user_id": user_id,
            "cost": cost,
            "quantity": quantity,
            "product_id": product_id,
            "item": product,
        }
        inventory_ref.add(new_item)
        return True
    except Exception as e:
        return False


def reduce_in_inventry(user_id: str, product_id: str, quantity: int) -> bool:
    """
    Reduces the quantity of a product in a user's inventory.
    Args:
        user_id (str): The ID of the user.
        product_id (str): The product ID.
        quantity (int): The quantity to reduce.
    Returns:
        bool: True if reduction was successful, False otherwise.
    """
    try:
        inventory_ref = db.collection("inventory")
        query = (
            inventory_ref.where("user_id", "==", user_id)
            .where("product_id", "==", product_id)
            .limit(1)
            .stream()
        )
        doc = next(query, None)
        if doc is None:

            return False
        data = doc.to_dict()
        current_quantity = data.get("quantity", 0)
        if current_quantity < quantity:
            return False
        new_quantity = current_quantity - quantity
        inventory_ref.document(doc.id).update({"quantity": new_quantity})
        return True
    except Exception as e:
        return False


def buy_item_from_seller(
    seller_id: str, cust_id: str, product_id: str, quantity: int
) -> bool:
    """
    Handles the purchase of an item from a seller by a customer.
    Args:
        seller_id (str): The ID of the seller.
        cust_id (str): The ID of the customer.
        product_id (str): The product ID.
        quantity (int): The quantity to buy.
    Returns:
        bool: True if the purchase was successful, False otherwise.
    """
    # Reduce inventory from seller
    if not reduce_in_inventry(seller_id, product_id, quantity):
        return False

    # Add item to customer's inventory
    try:
        inventory_ref = db.collection("inventory")
        query = (
            inventory_ref.where("user_id", "==", cust_id)
            .where("product_id", "==", product_id)
            .limit(1)
            .stream()
        )
        doc = next(query, None)
        if doc is None:
            # If customer doesn't have the product, create a new inventory entry
            inventory_ref.add(
                {"user_id": cust_id, "product_id": product_id, "quantity": quantity}
            )
        else:
            # If customer already has the product, update the quantity
            data = doc.to_dict()
            current_quantity = data.get("quantity", 0)
            new_quantity = current_quantity + quantity
            inventory_ref.document(doc.id).update({"quantity": new_quantity})

        return True
    except Exception as e:
        return False
