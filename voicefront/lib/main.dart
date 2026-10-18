import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'screens/chat_screen.dart';
import 'widgets/settings_drawer.dart';

import 'theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const VoiceFrontApp());
}

class VoiceFrontApp extends StatelessWidget {
  const VoiceFrontApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'VoiceFront AI (VF)',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme(),
      darkTheme: AppTheme.darkTheme(),
      themeMode: ThemeMode.system,
      home: const MainShell(),
    );
  }
}

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  Key _chatKey = UniqueKey();

  void _startNewChat() {
    setState(() {
      _chatKey = UniqueKey();
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Started new VF chat session.')),
    );
  }

  @override
  Widget build(BuildContext context) {
    // Status-bar icons follow the active theme. The previous implementation set
    // Brightness.dark once at startup, so icons disappeared in dark mode.
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final overlay = SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: isDark ? Brightness.light : Brightness.dark,
      statusBarBrightness: isDark ? Brightness.dark : Brightness.light,
    );

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: overlay,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('VF AI — VoiceFront Engine'),
          actions: [
            IconButton(
              icon: const Icon(Icons.add_comment_outlined),
              tooltip: 'New Chat',
              onPressed: _startNewChat,
            ),
          ],
        ),
        drawer: const VoiceFrontDrawer(),
        body: ChatScreen(key: _chatKey),
      ),
    );
  }
}
