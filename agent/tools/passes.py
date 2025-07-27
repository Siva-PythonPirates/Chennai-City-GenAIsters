import json
import requests
from typing import Literal
from google.cloud import firestore
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from utility.config import configurations

# Firestore client
db = firestore.Client()

# Google Wallet pass class IDs from config
RECEIPT_CLASS_ID = configurations["RECEIPT_CLASS_ID"]
REMINDER_CLASS_ID = configurations["REMINDER_CLASS_ID"]

# Google Wallet scopes and service account
GOOGLE_WALLET_SCOPES = ['https://www.googleapis.com/auth/wallet_object.issuer']
SERVICE_ACCOUNT_FILE = 'agent/tools/service_account.json'


def insert_pass_object_string(object_string: str, type: str) -> str:
    """
    Inserts a new pass object string into Firestore under the 'passes' collection.

    Args:
        object_string (str): JSON string representing the pass object (reminder or receipt).
        type (str): Type of pass, should be either "receipt" or "reminder".

    Returns:
        str: Auto-generated Firestore document ID where the object is stored.
    """
    doc_ref = db.collection("passes").document()
    doc_ref.set({
        "object": object_string,
        "type": type,
        "updated_at": firestore.SERVER_TIMESTAMP
    })
    return doc_ref.id


def get_pass_object_string(pass_type: Literal["receipt", "reminder"]) -> str:
    """
    Generates a default template JSON string for a receipt or reminder pass.

    Args:
        pass_type (Literal["receipt", "reminder"]): The type of pass to generate.

    Returns:
        str: JSON string template with placeholder values for the pass type.

    Raises:
        ValueError: If the pass_type is not "receipt" or "reminder".
    """
    if pass_type == "receipt":
        pass_string = {
            "dateAndTime": "<The exact date and time when the reminder should trigger>",
            "repeat": "<How often the reminder should repeat, such as 'Weekly', 'Monthly', 'Yearly', from the date and time it is set or 'None' if it's a one-time reminder.>",
            "title": "<A short title describing the reminder purpose, like 'Buy groceries' or 'Refuel bike.'>"
        }

    elif pass_type == "reminder":
        pass_string = {
            "date": "<The date and time when the receipt was issued. If unavailable, use the current date and time.>",
            "totalAmount": "<The total bill amount of the receipt. If unavailable, use 0.>",
            "items": [
                {
                    "name": "<The name of the item purchased. If unavailable, use 'MISC{n}' where 'n' is the item's index.>",
                    "quantity": "<The number of units purchased for this item. If unavailable, use 1.>",
                    "pricePerItem": "<The cost of one unit of the item.>"
                }
            ],
            "tax": "<The tax applied to all the items aggregated cost. If unavailable, use 0.>",
            "vendor": "<The name of the shop or vendor from which the purchase was made. If unavailable, use 'None'>",
            "otherDetails": "<Any additional extracted data such as payment mode (e.g., UPI, Card), bill number, item categories, or notes that can help AI better understand the receipt context>"
        }
    else:
        raise ValueError(f"Unsupported pass type: {pass_type}")

    return json.dumps(pass_string, indent=2)


def update_pass_object_string(object_id: str, object_dict: dict, type: str) -> dict:
    """
    Updates a pass object in Firestore and synchronizes it with the Google Wallet API.

    Args:
        object_id (str): Firestore document ID of the pass to update.
        object_dict (dict): The new pass object as a dictionary (not stringified).
        type (str): Type of pass ("receipt" or "reminder").

    Returns:
        dict: Status of the operation with object ID and any error details.
    """
    # Convert to JSON string for storing in Firestore
    object_json_str = json.dumps(object_dict, indent=2)

    # Save to Firestore
    db.collection("passes").document(object_id).set({
        "object": object_json_str,
        "type": type,
        "updated_at": firestore.SERVER_TIMESTAMP
    })

    # Set up credentials
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=GOOGLE_WALLET_SCOPES
    )
    authed_session = Request()
    credentials.refresh(authed_session)

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json"
    }

    # Post to Google Wallet
    response = requests.post(
        url="https://walletobjects.googleapis.com/walletobjects/v1/genericObject",
        headers=headers,
        data=json.dumps(object_dict)  # now valid JSON
    )

    if response.status_code == 200:
        return {"status": "updated_and_synced", "object_id": object_id}
    else:
        return {
            "status": "firebase_updated_but_google_wallet_failed",
            "google_error": response.text,
            "object_id": object_id
        }

    