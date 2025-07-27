import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:raseed_agent_app/receipt_view.dart';

class TransactionView extends StatefulWidget {
  final String buyerId;
  final String merchantId;
  final Map<String, int> cart;
  final List<Map<String, dynamic>> cartDetails;

  const TransactionView({
    super.key,
    required this.buyerId,
    required this.merchantId,
    required this.cart,
    required this.cartDetails,
  });

  @override
  State<TransactionView> createState() => _TransactionViewState();
}

class _TransactionViewState extends State<TransactionView> {
  final List<Map<String, String>> _messages = [];
  List<Map<String, String>> _conversationScript = [];

  @override
  void initState() {
    super.initState();
    // DEBUG PRINT
    print("--- 🚀 [TransactionView] initState: Screen Initialized ---");
    _buildDynamicScript();
    _startConversationAndTransaction();
  }

  void _buildDynamicScript() {
    // ... (This function remains the same as your version)
    const double mockNegotiation = 0.10;
    List<Map<String, String>> script = [];
    double subtotal = widget.cartDetails.fold(0, (sum, item) => sum + (item['price'] * item['quantity']));
    double discount = subtotal * mockNegotiation;
    double finalTotal = subtotal - discount;
    script.add({"sender": "Buying Agent", "text": "Hello! I'd like to purchase the following items."});
    String itemsText = widget.cartDetails.map((item) => "${item['quantity']}x ${item['productName']}").join('\n');
    script.add({"sender": "Buying Agent", "text": itemsText});
    script.add({"sender": "Payment Agent", "text": "Request received. Subtotal is \$${subtotal.toStringAsFixed(2)}. Verifying items with merchant..."});
    script.add({"sender": "Merchant Agent", "text": "All items are in stock. Ready to proceed."});
    script.add({"sender": "Payment Agent", "text": "Negotiating... a discount of \$${discount.toStringAsFixed(2)} has been applied."});
    script.add({"sender": "Payment Agent", "text": "The final total is \$${finalTotal.toStringAsFixed(2)}. Awaiting payment."});
    script.add({"sender": "Buying Agent", "text": "Excellent. Sending payment now."});
    setState(() {
      _conversationScript = script;
    });
     // DEBUG PRINT
    print("--- 💬 [TransactionView] _buildDynamicScript: Script generated with ${_conversationScript.length} steps. ---");
  }

  Future<void> _startConversationAndTransaction() async {
    // DEBUG PRINT
    print("--- ▶️ [TransactionView] _startConversationAndTransaction: Starting animation and API call ---");
    final apiCallFuture = _makeApiCall();

    for (final message in _conversationScript) {
      if(_messages.isEmpty) await Future.delayed(const Duration(milliseconds: 500));
      await Future.delayed(const Duration(milliseconds: 1800));
      if (mounted) {
        setState(() {
          _messages.add(message);
        });
      }
    }
    
    // DEBUG PRINT
    print("--- ⏳ [TransactionView] Waiting for API call to complete... ---");
    final result = await apiCallFuture;
    
    // DEBUG PRINT
    print("--- ✅ [TransactionView] API call completed with result: $result ---");

    if (mounted) {
      setState(() {
        _messages.add({
          "sender": result['status'],
          "text": result['message'],
        });
      });
    }

    await Future.delayed(const Duration(seconds: 3));

    if (mounted && result['status'] == 'Success') {
      final newTransactionId = result['transactionId'];
      Navigator.of(context)..pop()..pop();
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ReceiptView(transactionId: newTransactionId),
        ),
      );
    } else if (mounted) {
      Navigator.of(context).pop();
    }
  }
  
  Future<Map<String, dynamic>> _makeApiCall() async {
    // DEBUG PRINT
    print("--- 📞 [TransactionView] _makeApiCall: Preparing to send HTTP request... ---");
    final url = Uri.parse('https://3b5d635b89b7.ngrok-free.app/execute-transaction/');
    
    try {
      final cartItems = widget.cart.entries.map((entry) {
        return {'productId': entry.key, 'quantity': entry.value};
      }).toList();
      final requestBody = {
          'buyerId': widget.buyerId,
          'merchantId': widget.merchantId,
          'cart': cartItems,
      };

      // DEBUG PRINT
      print("   - Calling URL: $url");
      print("   - Request Body: ${json.encode(requestBody)}");

      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: json.encode(requestBody),
      );
      
      final responseBody = json.decode(response.body);

      // DEBUG PRINT
      print("--- 📥 [TransactionView] Server Response Received ---");
      print("   - Status Code: ${response.statusCode}");
      print("   - Response Body: ${response.body}");

      if (response.statusCode == 200 && responseBody['status'] == 'success') {
        final receipt = responseBody['buyer_receipt'];
        return {
          "status": "Success",
          "message": "Payment Confirmed. Thank you!",
          "transactionId": receipt['transactionId'],
        };
      } else {
        final errorMessage = responseBody['detail'] ?? 'An unknown error occurred.';
        return {
          "status": "Failed",
          "message": "Transaction Failed: $errorMessage"
        };
      }
    } catch (e) {
      // DEBUG PRINT
      print("--- ❌ [TransactionView] CATCH BLOCK ERROR: Could not connect or parse response. ---");
      print("   - Error Details: ${e.toString()}");
      return {"status": "Failed", "message": "Error: Could not connect to server."};
    }
  }

  @override
  Widget build(BuildContext context) {
    // ... build method and ChatBubble widget remain the same as your version
    return Scaffold(
      appBar: AppBar(
        title: const Text('Completing Your Order...'),
        automaticallyImplyLeading: false,
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(16.0),
        itemCount: _messages.length,
        itemBuilder: (context, index) {
          final message = _messages[index];
          return ChatBubble(
            sender: message['sender']!,
            text: message['text']!,
          );
        },
      ),
    );
  }
}

class ChatBubble extends StatelessWidget {
  final String sender;
  final String text;
  const ChatBubble({super.key, required this.sender, required this.text});

  @override
  Widget build(BuildContext context) {
    final bool isStatusMessage = sender == 'Success' || sender == 'Failed';
    final bool isBuyer = sender == 'Buying Agent';
    final bool isMerchant = sender == 'Merchant Agent';
    final bool isSystem = sender == 'Payment Agent';
    
    Color bubbleColor = Colors.grey;
    if (isSystem) bubbleColor = Colors.blueGrey;
    if (isBuyer) bubbleColor = Colors.teal;
    if (isMerchant) bubbleColor = Colors.indigo;

    final Alignment alignment = isSystem || isStatusMessage ? Alignment.center : (isBuyer ? Alignment.centerRight : Alignment.centerLeft);
    
    if (isStatusMessage) {
      return Center(
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 8),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: sender == 'Success' ? Colors.green.shade700 : Colors.red.shade700,
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(text, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        ),
      );
    }
    
    if (isSystem) {
       return Center(
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 8),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: Colors.blueGrey.shade700,
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(text, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontStyle: FontStyle.italic)),
        ),
      );
    }

    return Align(
      alignment: alignment,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: bubbleColor,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: isBuyer ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(sender, style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white.withOpacity(0.8), fontSize: 12)),
            const SizedBox(height: 4),
            Text(text, style: const TextStyle(color: Colors.white, fontSize: 16)),
          ],
        ),
      ),
    );
  }
}