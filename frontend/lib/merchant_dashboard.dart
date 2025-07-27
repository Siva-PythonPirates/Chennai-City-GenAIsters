import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:raseed_agent_app/auth_service.dart';
import 'package:raseed_agent_app/receipt_view.dart';
import 'package:intl/intl.dart';

class MerchantDashboard extends StatefulWidget {
  final Map<String, dynamic> userData;
  const MerchantDashboard({super.key, required this.userData});

  @override
  State<MerchantDashboard> createState() => _MerchantDashboardState();
}

class _MerchantDashboardState extends State<MerchantDashboard> {
  final _productNameController = TextEditingController();
  final _productPriceController = TextEditingController();

  late final Stream<QuerySnapshot> _salesStream;

  @override
  void initState() {
    super.initState();
    final user = FirebaseAuth.instance.currentUser;
    _salesStream = FirebaseFirestore.instance
        .collection('transactions')
        .where('merchantId', isEqualTo: user!.uid)
        .orderBy('timestamp', descending: true)
        .limit(10)
        .snapshots(includeMetadataChanges: true);
  }

  void _addProductDialog() {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('List a New Product'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _productNameController,
                decoration: const InputDecoration(labelText: 'Product Name'),
              ),
              TextField(
                controller: _productPriceController,
                decoration: const InputDecoration(labelText: 'Price'),
                keyboardType: TextInputType.number,
              ),
            ],
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Cancel')),
            ElevatedButton(
                onPressed: _addProduct, child: const Text('Add Product')),
          ],
        );
      },
    );
  }

  void _addProduct() {
    final user = FirebaseAuth.instance.currentUser;
    final name = _productNameController.text;
    final price = double.tryParse(_productPriceController.text);

    if (name.isNotEmpty && price != null && price > 0 && user != null) {
      FirebaseFirestore.instance.collection('products').add({
        'merchantId': user.uid,
        'merchantName': widget.userData['name'],
        'productName': name,
        'price': price,
        'quantity': 100,
      });
      _productNameController.clear();
      _productPriceController.clear();
      Navigator.pop(context);
    }
  }

  void _deleteProduct(String productId, String productName) {
     showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Remove Product'),
        content: Text('Are you sure you want to remove "$productName"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              FirebaseFirestore.instance
                  .collection('products')
                  .doc(productId)
                  .delete();
              Navigator.pop(context);
            },
            child: const Text('Remove', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authService = AuthService();
    final user = FirebaseAuth.instance.currentUser;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Merchant Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => authService.signOut(),
          )
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _addProductDialog,
        label: const Text('Add Product'),
        icon: const Icon(Icons.add),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              elevation: 4,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('BUSINESS BALANCE',
                            style: TextStyle(color: Colors.white70)),
                        const SizedBox(height: 8),
                        Text(widget.userData['name'],
                            style: const TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: Colors.white)),
                      ],
                    ),
                    Text(
                      '\$${widget.userData['walletBalance'].toStringAsFixed(2)}',
                      style: const TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.bold,
                          color: Colors.tealAccent),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            const Text('Your Products for Sale',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            StreamBuilder<QuerySnapshot>(
              stream: FirebaseFirestore.instance
                  .collection('products')
                  .where('merchantId', isEqualTo: user!.uid)
                  .snapshots(),
              builder: (context, snapshot) {
                if (!snapshot.hasData)
                  return const Center(child: CircularProgressIndicator());
                if (snapshot.data!.docs.isEmpty) {
                  return const Center(
                      child: Text('You have no products listed.'));
                }
                final products = snapshot.data!.docs;
                return ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: products.length,
                  itemBuilder: (context, index) {
                    final product = products[index];
                    return Card(
                      margin: const EdgeInsets.symmetric(vertical: 4),
                      child: ListTile(
                        leading: const Icon(Icons.inventory_2_outlined,
                            color: Colors.blueAccent),
                        title: Text(product['productName']),
                        subtitle:
                            Text('Stock: ${product['quantity'].toString()}'),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                                '\$${product['price'].toStringAsFixed(2)}'),
                            IconButton(
                              icon: const Icon(Icons.delete_outline,
                                  color: Colors.redAccent),
                              onPressed: () => _deleteProduct(
                                  product.id, product['productName']),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                );
              },
            ),
            const SizedBox(height: 24),

            const Text('Recent Sales',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            StreamBuilder<QuerySnapshot>(
              stream: _salesStream,
              builder: (context, snapshot) {
                if (snapshot.hasError) return const Text("Error loading sales.");
                if (!snapshot.hasData)
                  return const Center(child: CircularProgressIndicator());
                if (snapshot.data!.docs.isEmpty) {
                  return const Center(
                      child: Text('You haven\'t made any sales yet.'));
                }
                final transactions = snapshot.data!.docs;
                return ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: transactions.length,
                  itemBuilder: (context, index) {
                    final tx = transactions[index];
                    final timestamp = (tx['timestamp'] as Timestamp).toDate();
                    return Card(
                      margin: const EdgeInsets.symmetric(vertical: 4),
                      child: ListTile(
                        leading: const Icon(Icons.point_of_sale,
                            color: Colors.tealAccent),
                        title: Text('Sale to ${tx['buyerName']}'),
                        subtitle: Text(
                            DateFormat.yMMMd().add_jm().format(timestamp)),
                        trailing: Text(
                            '+\$${tx['finalTotal'].toStringAsFixed(2)}',
                            style: const TextStyle(color: Colors.greenAccent)),
                        onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                                builder: (_) =>
                                    ReceiptView(transactionId: tx.id))),
                      ),
                    );
                  },
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}