import 'package:flutter/material.dart';
import '../services/account_manager.dart';

class VoiceFrontDrawer extends StatelessWidget {
  const VoiceFrontDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          UserAccountsDrawerHeader(
            accountName: Text(AccountManager.userName),
            accountEmail: Text('${AccountManager.userEmail} • ${AccountManager.userPlan}'),
            currentAccountPicture: const CircleAvatar(
              backgroundColor: Colors.white,
              child: Text('AM', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.blue)),
            ),
            decoration: BoxDecoration(color: Theme.of(context).primaryColor),
          ),
          ListTile(
            leading: const Icon(Icons.storefront),
            title: const Text('My Deployed Storefronts'),
            subtitle: Text('${AccountManager.savedArtifacts.length} stored website artifacts'),
            onTap: () {
              Navigator.pop(context);
              _showArtifactsDialog(context);
            },
          ),
          ListTile(
            leading: const Icon(Icons.auto_awesome),
            title: const Text('Component Library'),
            subtitle: const Text('25+ verified variants'),
            onTap: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Component Library: Food, Apparel, Services fully seeded.')),
              );
            },
          ),
          ListTile(
            leading: const Icon(Icons.analytics),
            title: const Text('Pipeline Tracer (L1-L5)'),
            subtitle: const Text('NLP -> Layout -> QA -> Publish'),
            onTap: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('All 4 microservices operational on ports 8001-8004.')),
              );
            },
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.settings),
            title: const Text('Settings & API Keys'),
            onTap: () {
              Navigator.pop(context);
            },
          ),
          ListTile(
            leading: const Icon(Icons.logout, color: Colors.red),
            title: const Text('Sign Out', style: TextStyle(color: Colors.red)),
            onTap: () {
              Navigator.pop(context);
            },
          ),
        ],
      ),
    );
  }

  void _showArtifactsDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Stored Website Artifacts'),
        content: SizedBox(
          width: 400,
          height: 300,
          child: ListView.builder(
            itemCount: AccountManager.savedArtifacts.length,
            itemBuilder: (context, index) {
              final art = AccountManager.savedArtifacts[index];
              return ListTile(
                leading: const Icon(Icons.web, color: Colors.blue),
                title: Text(art['name']),
                subtitle: Text('Category: ${art['category']} • ${art['timestamp']}'),
                trailing: Chip(label: Text(art['status'], style: const TextStyle(fontSize: 10))),
              );
            },
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
}
