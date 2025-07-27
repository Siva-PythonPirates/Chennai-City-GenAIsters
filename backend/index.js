const functions = require("firebase-functions");
const admin = require("firebase-admin");
admin.initializeApp();

const db = admin.firestore();

exports.executeTransaction = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError(
      "unauthenticated", "You must be logged in to make a purchase."
    );
  }

  const { merchantId, items } = data; // items = [{ productId: "...", quantity: 2 }]
  const buyerId = context.auth.uid;

  if (!merchantId || !items || items.length === 0) {
    throw new functions.https.HttpsError("invalid-argument", "Missing merchant or item data.");
  }

  return db.runTransaction(async (t) => {
    const buyerRef = db.collection("users").doc(buyerId);
    const merchantRef = db.collection("users").doc(merchantId);
    const buyerDoc = await t.get(buyerRef);
    const merchantDoc = await t.get(merchantRef);

    if (!buyerDoc.exists || !merchantDoc.exists) {
      throw new functions.https.HttpsError("not-found", "User not found.");
    }

    let originalTotal = 0;
    const purchasedItemsInfo = [];
    const productUpdates = [];

    for (const item of items) {
      const productRef = db.collection("products").doc(item.productId);
      const productDoc = await t.get(productRef);
      if (!productDoc.exists || productDoc.data().merchantId !== merchantId) {
        throw new functions.https.HttpsError("not-found", `Product ID ${item.productId} not found for this merchant.`);
      }
      const productData = productDoc.data();
      if (productData.quantity < item.quantity) {
          throw new functions.https.HttpsError("failed-precondition", `Not enough stock for ${productData.productName}.`);
      }
      originalTotal += productData.price * item.quantity;
      purchasedItemsInfo.push({
        productName: productData.productName,
        quantity: item.quantity,
        price: productData.price,
      });
      // Prepare to update product quantity
      const newQuantity = productData.quantity - item.quantity;
      productUpdates.push({ ref: productRef, newQuantity: newQuantity });
    }

    const buyerLimit = buyerDoc.data().negotiationLimit;
    const merchantLimit = merchantDoc.data().negotiationLimit;
    const agreedDiscountPercentage = (buyerLimit + merchantLimit) / 2;
    const negotiatedDiscount = originalTotal * agreedDiscountPercentage;
    const finalTotal = originalTotal - negotiatedDiscount;

    const buyerWallet = buyerDoc.data().walletBalance;
    if (buyerWallet < finalTotal) {
      throw new functions.https.HttpsError("failed-precondition", "Insufficient funds.");
    }

    const newBuyerBalance = buyerWallet - finalTotal;
    const newMerchantBalance = merchantDoc.data().walletBalance + finalTotal;

    // --- Execute all updates ---
    t.update(buyerRef, { walletBalance: newBuyerBalance });
    t.update(merchantRef, { walletBalance: newMerchantBalance });
    productUpdates.forEach(update => t.update(update.ref, { quantity: update.newQuantity }));

    const receiptRef = db.collection("transactions").doc();
    t.set(receiptRef, {
      buyerId: buyerId,
      merchantId: merchantId,
      buyerName: buyerDoc.data().name,
      merchantName: merchantDoc.data().name,
      items: purchasedItemsInfo,
      originalTotal: originalTotal,
      negotiatedDiscount: negotiatedDiscount,
      finalTotal: finalTotal,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
    });

    return {
      success: true,
      message: "Transaction successful! Receipt generated.",
      receiptId: receiptRef.id,
    };
  });
});