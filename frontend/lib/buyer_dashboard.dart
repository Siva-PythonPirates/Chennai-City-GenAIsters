import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:raseed_agent_app/auth_service.dart';
import 'package:raseed_agent_app/merchant_store_screen.dart';
import 'package:raseed_agent_app/receipt_view.dart';

class BuyerDashboard extends StatefulWidget {
  final Map<String, dynamic> userData;
  const BuyerDashboard({super.key, required this.userData});

  @override
  State<BuyerDashboard> createState() => _BuyerDashboardState();
}

class _BuyerDashboardState extends State<BuyerDashboard> {
  late final Stream<QuerySnapshot> _transactionsStream;

  @override
  void initState() {
    super.initState();
    final user = FirebaseAuth.instance.currentUser;
    _transactionsStream = FirebaseFirestore.instance
        .collection('transactions')
        .where('buyerId', isEqualTo: user!.uid)
        .orderBy('timestamp', descending: true)
        .limit(10)
        .snapshots(includeMetadataChanges: true);
  }

  @override
  Widget build(BuildContext context) {
    final authService = AuthService();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Buyer Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => authService.signOut(),
          )
        ],
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
                        const Text('WALLET BALANCE',
                            style: TextStyle(color: Colors.white70)),
                        const SizedBox(height: 8),
                        const Text('Welcome back,',
                            style: TextStyle(color: Colors.white70)),
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

            const Text('Available Merchants',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            SizedBox(
              height: 150,
              child: StreamBuilder<QuerySnapshot>(
                stream: FirebaseFirestore.instance
                    .collection('users')
                    .where('role', isEqualTo: 'merchant')
                    .snapshots(),
                builder: (context, snapshot) {
                  if (!snapshot.hasData) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  final merchants = snapshot.data!.docs;
                  return ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: merchants.length,
                    itemBuilder: (context, index) {
                      final merchant = merchants[index];
                      return Card(
                        child: InkWell(
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => MerchantStoreScreen(
                                  merchantId: merchant.id,
                                  merchantName: merchant['name'],
                                  buyerWalletBalance: widget
                                      .userData['walletBalance']
                                      .toDouble(),
                                ),
                              ),
                            );
                          },
                          child: Container(
                            width: 200,
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.store,
                                    size: 40, color: Colors.tealAccent),
                                const SizedBox(height: 10),
                                Text(merchant['name'],
                                    textAlign: TextAlign.center,
                                    style: const TextStyle(
                                        fontWeight: FontWeight.bold)),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  );
                },
              ),
            ),
            const SizedBox(height: 24),

            const Text('Recent Buys',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            StreamBuilder<QuerySnapshot>(
              stream: _transactionsStream,
              builder: (context, snapshot) {
                if (snapshot.hasError) {
                  return const Center(
                      child: Text(
                          "Error fetching transactions. Is the index created?"));
                }
                if (!snapshot.hasData) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.data!.docs.isEmpty) {
                  return const Center(
                      child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Text('You haven\'t made any purchases yet.'),
                  ));
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
                        leading: const Icon(Icons.receipt_long,
                            color: Colors.tealAccent),
                        title: Text('Purchase from ${tx['merchantName']}'),
                        subtitle: Text(
                            DateFormat.yMMMd().add_jm().format(timestamp)),
                        trailing: Text(
                            '-\$${tx['finalTotal'].toStringAsFixed(2)}',
                            style: const TextStyle(color: Colors.redAccent)),
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