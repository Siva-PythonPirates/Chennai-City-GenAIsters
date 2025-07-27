import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

class ReceiptView extends StatelessWidget {
  final String transactionId;

  const ReceiptView({super.key, required this.transactionId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Transaction Receipt")),
      body: FutureBuilder<DocumentSnapshot>(
        future: FirebaseFirestore.instance
            .collection('transactions')
            .doc(transactionId)
            .get(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!snapshot.data!.exists) {
            return const Center(child: Text("Receipt not found."));
          }

          final data = snapshot.data!.data() as Map<String, dynamic>;
          final items = data['items'] as List;
          final timestamp = (data['timestamp'] as Timestamp).toDate();

          return Padding(
            padding: const EdgeInsets.all(16.0),
            child: Card(
              elevation: 0,
              color: Theme.of(context).colorScheme.surface,
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Center(
                      child: Icon(Icons.check_circle,
                          color: Colors.green, size: 60),
                    ),
                    const SizedBox(height: 16),
                    Center(
                      child: Text(
                        "Transaction Complete",
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                    ),
                    Center(
                        child: Text(
                            DateFormat.yMMMd().add_jm().format(timestamp))),
                    const Divider(height: 40),
                    Text(
                      "Sold By: ${data['merchantName']}",
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    Text("Purchased By: ${data['buyerName']}"),
                    const Divider(height: 30),
                    const Text("Items:",
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    ...items.map((item) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 2.0),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                  "${item['productName']} (x${item['quantity']})"),
                              Text(
                                  "\$${(item['price'] * item['quantity']).toStringAsFixed(2)}"),
                            ],
                          ),
                        )),
                    const Divider(height: 30),
                    _buildTotalRow("Subtotal:",
                        "\$${data['originalTotal'].toStringAsFixed(2)}"),
                    _buildTotalRow("Negotiated Discount:",
                        "-\$${data['negotiatedDiscount'].toStringAsFixed(2)}",
                        color: Colors.greenAccent),
                    const SizedBox(height: 10),
                    _buildTotalRow("Final Total:",
                        "\$${data['finalTotal'].toStringAsFixed(2)}",
                        isBold: true,
                        size: 20),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildTotalRow(String title, String amount,
      {Color color = Colors.white, bool isBold = false, double size = 16}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(title,
              style: TextStyle(
                  fontSize: size,
                  fontWeight: isBold ? FontWeight.bold : FontWeight.normal)),
          Text(amount,
              style: TextStyle(
                  color: color,
                  fontSize: size,
                  fontWeight: isBold ? FontWeight.bold : FontWeight.bold)),
        ],
      ),
    );
  }
}