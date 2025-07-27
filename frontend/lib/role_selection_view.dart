import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

class RoleSelectionView extends StatelessWidget {
  const RoleSelectionView({super.key});

  Future<void> _selectRole(BuildContext context, String role) async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return;

    try {
      await FirebaseFirestore.instance
          .collection('users')
          .doc(user.uid)
          .update({'role': role});
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to set role: $e')),
      );
    }
  }

  Widget _buildRoleCard({
    required BuildContext context,
    required String role,
    required String description,
    required IconData icon,
    required Color color,
  }) {
    return Card(
      elevation: 5,
      child: InkWell(
        onTap: () => _selectRole(context, role.toLowerCase()),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 40),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 60, color: color),
              const SizedBox(height: 15),
              Text(
                role,
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),
              Text(
                description,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white70, fontSize: 16),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Choose Your Role',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 15),
            const Text(
              'This choice is permanent for this account.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white70, fontSize: 16),
            ),
            const SizedBox(height: 50),
            _buildRoleCard(
              context: context,
              role: 'Buyer',
              description: 'Browse merchants and purchase goods.',
              icon: Icons.shopping_cart_checkout,
              color: Colors.tealAccent,
            ),
            const SizedBox(height: 30),
            _buildRoleCard(
              context: context,
              role: 'Merchant',
              description: 'List products and track your sales.',
              icon: Icons.storefront,
              color: Colors.blueAccent,
            ),
          ],
        ),
      ),
    );
  }
}