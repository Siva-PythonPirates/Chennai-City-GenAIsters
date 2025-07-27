import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:raseed_agent_app/transaction_view.dart';

class Product {
  final String id;
  final String name;
  final double price;
  final int stock;
  Product(
      {required this.id,
      required this.name,
      required this.price,
      required this.stock});

  factory Product.fromFirestore(DocumentSnapshot doc) {
    Map data = doc.data() as Map<String, dynamic>;
    return Product(
      id: doc.id,
      name: data['productName'] ?? '',
      price: (data['price'] ?? 0.0).toDouble(),
      stock: (data['quantity'] ?? 0).toInt(),
    );
  }
}

class MerchantStoreScreen extends StatefulWidget {
  final String merchantId;
  final String merchantName;
  final double buyerWalletBalance;
  const MerchantStoreScreen(
      {super.key,
      required this.merchantId,
      required this.merchantName,
      required this.buyerWalletBalance});

  @override
  State<MerchantStoreScreen> createState() => _MerchantStoreScreenState();
}

class _MerchantStoreScreenState extends State<MerchantStoreScreen> {
  final Map<String, int> _cart = {};
  double _cartTotal = 0.0;
  List<Product> _availableProducts = [];

  void _addToCart(Product product) {
    if ((_cartTotal + product.price) > widget.buyerWalletBalance) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Insufficient wallet balance!'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }
    final currentQuantityInCart = _cart[product.id] ?? 0;
    if (currentQuantityInCart >= product.stock) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('No more "${product.name}" in stock!'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }
    setState(() {
      _cart.update(product.id, (value) => value + 1, ifAbsent: () => 1);
      _cartTotal += product.price;
    });
  }

  void _removeFromCart(Product product) {
    if (!_cart.containsKey(product.id)) return;
    setState(() {
      if (_cart[product.id]! > 1) {
        _cart[product.id] = _cart[product.id]! - 1;
      } else {
        _cart.remove(product.id);
      }
      _cartTotal -= product.price;
    });
  }

  void _executePurchase() {
    if (_cart.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Your cart is empty.')),
      );
      return;
    }

    final buyerId = FirebaseAuth.instance.currentUser!.uid;

    final List<Map<String, dynamic>> cartDetails = [];
    _cart.forEach((productId, quantity) {
      final product = _availableProducts.firstWhere((p) => p.id == productId,
          orElse: () => Product(id: '', name: 'Unknown', price: 0, stock: 0));
      cartDetails.add({
        'productName': product.name,
        'quantity': quantity,
        'price': product.price,
      });
    });

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => TransactionView(
          buyerId: buyerId,
          merchantId: widget.merchantId,
          cart: _cart,
          cartDetails: cartDetails,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.merchantName),
      ),
      body: Column(
        children: [
          Expanded(
            child: StreamBuilder<QuerySnapshot>(
              stream: FirebaseFirestore.instance
                  .collection('products')
                  .where('merchantId', isEqualTo: widget.merchantId)
                  .snapshots(),
              builder: (context, snapshot) {
                if (!snapshot.hasData) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.data!.docs.isEmpty) {
                  return const Center(
                      child: Text("This merchant has no products."));
                }
                
                _availableProducts = snapshot.data!.docs
                    .map((doc) => Product.fromFirestore(doc))
                    .toList();

                return ListView.builder(
                  itemCount: _availableProducts.length,
                  itemBuilder: (context, index) {
                    final product = _availableProducts[index];
                    final quantityInCart = _cart[product.id] ?? 0;
                    return ListTile(
                      title: Text(product.name),
                      subtitle: Text(
                          '\$${product.price.toStringAsFixed(2)} - Stock: ${product.stock}'),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.remove_circle_outline),
                            onPressed: () => _removeFromCart(product),
                          ),
                          Text(quantityInCart.toString(),
                              style: const TextStyle(fontSize: 18)),
                          IconButton(
                            icon: const Icon(Icons.add_circle),
                            onPressed: () => _addToCart(product),
                          ),
                        ],
                      ),
                    );
                  },
                );
              },
            ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              boxShadow: const [
                BoxShadow(
                    color: Colors.black26,
                    blurRadius: 10,
                    offset: Offset(0, -2))
              ],
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('TOTAL',
                        style: TextStyle(color: Colors.white70)),
                    Text(
                      '\$${_cartTotal.toStringAsFixed(2)}',
                      style: const TextStyle(
                          fontSize: 24, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                ElevatedButton.icon(
                  onPressed: _executePurchase,
                  icon: const Icon(Icons.shopping_bag_outlined),
                  label: const Text('Proceed to Buy'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 24, vertical: 12),
                  ),
                )
              ],
            ),
          )
        ],
      ),
    );
  }
}