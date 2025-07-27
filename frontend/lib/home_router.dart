import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:raseed_agent_app/buyer_dashboard.dart';
import 'package:raseed_agent_app/merchant_dashboard.dart';
import 'package:raseed_agent_app/role_selection_view.dart';

class HomeRouter extends StatelessWidget {
  HomeRouter({super.key});

  final user = FirebaseAuth.instance.currentUser;

  @override
  Widget build(BuildContext context) {
    if (user == null) {
      return const Scaffold(body: Center(child: Text("Not logged in.")));
    }

    return StreamBuilder<DocumentSnapshot>(
      stream: FirebaseFirestore.instance
          .collection('users')
          .doc(user!.uid)
          .snapshots(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
              body: Center(child: CircularProgressIndicator()));
        }
        if (!snapshot.hasData || !snapshot.data!.exists) {
          return const Scaffold(
              body: Center(child: Text("Setting up your account...")));
        }

        final userData = snapshot.data!.data() as Map<String, dynamic>;
        final String role = userData['role'] ?? 'none';

        if (role == 'merchant') {
          return MerchantDashboard(userData: userData);
        } else if (role == 'buyer') {
          return BuyerDashboard(userData: userData);
        } else {
          return const RoleSelectionView();
        }
      },
    );
  }
}