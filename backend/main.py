import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# --- Pydantic Models for Data Validation ---
class CartItem(BaseModel):
    productId: str
    quantity: int

class TransactionRequest(BaseModel):
    buyerId: str
    merchantId: str
    cart: List[CartItem]

class ReceiptItem(BaseModel):
    productName: str
    quantity: int
    price: float

class Receipt(BaseModel):
    transactionId: str
    buyerName: str
    merchantName: str
    items: List[ReceiptItem]
    originalTotal: float
    negotiatedDiscount: float
    finalTotal: float
    timestamp: str

class TransactionResponse(BaseModel):
    status: str
    message: str
    conversation_log: List[str]
    buyer_receipt: Receipt | None = None
    merchant_receipt: Receipt | None = None

# --- Initialize FastAPI and Firebase Admin SDK ---
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()


# --- Decorated Transaction Function ---
@firestore.transactional
def process_transaction(transaction, request, log):
    # --- 1. Gather all document references ---
    buyer_ref = db.collection("users").document(request.buyerId)
    merchant_ref = db.collection("users").document(request.merchantId)
    product_refs = [db.collection("products").document(item.productId) for item in request.cart]
    
    # --- 2. Read all documents in one batch ---
    all_refs_to_get = [buyer_ref, merchant_ref] + product_refs
    all_snapshots = transaction.get_all(all_refs_to_get)

    docs_by_id = {snap.id: snap for snap in all_snapshots if snap.exists}

    buyer_doc_snapshot = docs_by_id.get(request.buyerId)
    merchant_doc_snapshot = docs_by_id.get(request.merchantId)

    if not buyer_doc_snapshot or not merchant_doc_snapshot:
        raise HTTPException(status_code=404, detail="Buyer or Merchant account not found.")

    buyer_doc = buyer_doc_snapshot.to_dict()
    merchant_doc = merchant_doc_snapshot.to_dict()

    # --- 3. Validate products and calculate totals ---
    original_total = 0.0
    purchased_items = []
    product_updates = []

    for item in request.cart:
        product_snapshot = docs_by_id.get(item.productId)
        if not product_snapshot:
            raise HTTPException(status_code=404, detail=f"Product {item.productId} not found.")
        
        product_doc = product_snapshot.to_dict()
        
        if product_doc.get('merchantId') != request.merchantId:
            raise HTTPException(status_code=400, detail=f"Product {product_doc.get('productName')} does not belong to this merchant.")
        if product_doc.get('quantity', 0) < item.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for {product_doc.get('productName')}.")

        original_total += product_doc.get('price', 0) * item.quantity
        purchased_items.append({"productName": product_doc.get('productName'), "quantity": item.quantity, "price": product_doc.get('price')})
        product_updates.append({"ref": product_snapshot.reference, "new_quantity": product_doc.get('quantity') - item.quantity})

    # --- 4. Dynamic Bargaining Conversation & Calculation ---
    log.append({"sender": "Buying Agent", "text": f"Requesting to buy {len(purchased_items)} item(s) for a total of ${original_total:.2f}."})
    log.append({"sender": "Merchant Agent", "text": "Request received. All items are in stock. Let me see what I can do on the price."})
    
    buyer_limit = buyer_doc.get('negotiationLimit', 0)
    merchant_limit = merchant_doc.get('negotiationLimit', 0)
    discount_percentage = (buyer_limit + merchant_limit) / 2
    negotiated_discount = original_total * discount_percentage
    final_total = original_total - negotiated_discount

    merchant_offer = original_total * (merchant_limit * 0.5)
    log.append({"sender": "Merchant Agent", "text": f"How about ${original_total - merchant_offer:.2f}?"})
    log.append({"sender": "Buying Agent", "text": f"That's a good start. Can you do ${final_total:.2f}?"})
    log.append({"sender": "Merchant Agent", "text": f"You drive a hard bargain! Okay, ${final_total:.2f} it is. Deal."})

    # --- 5. Check wallet and execute updates ---
    if buyer_doc.get('walletBalance', 0) < final_total:
        raise HTTPException(status_code=400, detail="Insufficient funds.")
    
    log.append({"sender": "Buying Agent", "text": "Excellent. Sending payment now."})
    
    new_buyer_balance = buyer_doc.get('walletBalance') - final_total
    new_merchant_balance = merchant_doc.get('walletBalance') + final_total
    
    transaction.update(buyer_ref, {'walletBalance': new_buyer_balance})
    transaction.update(merchant_ref, {'walletBalance': new_merchant_balance})
    for update in product_updates:
        transaction.update(update['ref'], {'quantity': update['new_quantity']})
    
    log.append({"sender": "Merchant Agent", "text": "Payment received. Thank you for your business!"})

    # --- 6. Create receipt record ---
    receipt_ref = db.collection("transactions").document()
    
    receipt_data = {
        "transactionId": receipt_ref.id, "buyerName": buyer_doc.get('name'), "merchantName": merchant_doc.get('name'),
        "items": purchased_items, "originalTotal": original_total, "negotiatedDiscount": negotiated_discount,
        "finalTotal": final_total, "timestamp": firestore.SERVER_TIMESTAMP
    }
    transaction.set(receipt_ref, receipt_data)
    
    return receipt_data


# --- API Endpoint ---
@app.post("/execute-transaction/", response_model=TransactionResponse)
async def execute_transaction(request: TransactionRequest):
    conversation_log_dicts = []
    
    try:
        transaction = db.transaction()
        final_receipt_data = process_transaction(transaction, request, conversation_log_dicts)

        final_receipt_data['timestamp'] = "Just now" 
        receipt = Receipt(**final_receipt_data)

        # Flatten the conversation log for the response model
        conversation_log_flat = [f"{msg['sender']}: {msg['text']}" for msg in conversation_log_dicts]

        return TransactionResponse(
            status="success",
            message="Transaction completed successfully!",
            conversation_log=conversation_log_flat,
            buyer_receipt=receipt,
            merchant_receipt=receipt,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {e}")