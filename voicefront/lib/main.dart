import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'theme/app_theme.dart';
import 'screens/home_screen.dart';
import 'screens/record_screen.dart';
import 'screens/review_edit_screen.dart';
import 'screens/preview_qa_screen.dart';
import 'screens/storefronts_screen.dart';
import 'widgets/bottom_nav_bar.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );
  runApp(const VoiceFrontApp());
}

class VoiceFrontApp extends StatelessWidget {
  const VoiceFrontApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'VoiceFront',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.theme,
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
  int _currentNavIndex = 0;

  void _onNavTap(int index) {
    setState(() => _currentNavIndex = index);
  }

  void _navigateToRecord() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => RecordScreen(
          onNavigateToReview: () {
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(
                builder: (_) => ReviewEditScreen(
                  onNavigateToPreview: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => PreviewQAScreen(
                          onPublish: () {
                            Navigator.of(context).popUntil((r) => r.isFirst);
                            setState(() => _currentNavIndex = 2);
                          },
                        ),
                      ),
                    );
                  },
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildCurrentScreen() {
    switch (_currentNavIndex) {
      case 0:
        return HomeScreen(
          onNavigateToRecord: _navigateToRecord,
          onNavigateToStorefronts: () => _onNavTap(2),
        );
      case 1:
        return RecordScreen(
          onNavigateToReview: () {
            Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => ReviewEditScreen(
                  onNavigateToPreview: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => PreviewQAScreen(
                          onPublish: () {
                            Navigator.of(context).popUntil((r) => r.isFirst);
                            setState(() => _currentNavIndex = 2);
                          },
                        ),
                      ),
                    );
                  },
                ),
              ),
            );
          },
        );
      case 2:
        return StorefrontsScreen(
          onNewStore: _navigateToRecord,
        );
      case 3:
        return const _SettingsPlaceholder();
      default:
        return HomeScreen(
          onNavigateToRecord: _navigateToRecord,
          onNavigateToStorefronts: () => _onNavTap(2),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _buildCurrentScreen(),
      bottomNavigationBar: VoiceFrontBottomNav(
        currentIndex: _currentNavIndex,
        onTap: _onNavTap,
      ),
    );
  }
}

class _SettingsPlaceholder extends StatelessWidget {
  const _SettingsPlaceholder();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.settings_rounded, size: 64, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text(
            'Settings',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w600,
              color: Colors.grey[500],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Coming soon',
            style: TextStyle(
              fontSize: 14,
              color: Colors.grey[400],
            ),
          ),
        ],
      ),
    );
  }
}
