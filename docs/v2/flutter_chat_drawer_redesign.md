# Flutter App UI Redesign: ChatGPT-Style Chat Interface & Navigation Drawer

## 1. Design Shift
We are upgrading `voicefront/` from a 4-tab bottom navigation bar (`HomeScreen`, `RecordScreen`, `StorefrontsScreen`, `Settings`) into a **ChatGPT-inspired Conversational Interface**:
- **Primary Screen (`ChatScreen`)**: Clean chat stream where users converse with Tony to build storefronts via text or voice. Features live in-app WebView sandbox previews directly in the chat stream.
- **Side Drawer (`Drawer`)**: Tucked away neatly behind a hamburger menu in the top app bar. Contains:
  - User Profile & Login details (`user@voicefront.ai`)
  - "My Storefronts" (list of active/published sites)
  - Component Intelligence Inspector (Scrapling + REA stats)
  - Pipeline Tracer / Developer Mode
  - Settings & API configurations

---

## 2. Updated Flutter Widget Tree (`voicefront/lib/main.dart`)

```dart
class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  // We replace bottom navigation with a clean ChatScreen + Side Drawer
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('VoiceFront AI'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add_comment_outlined),
            onPressed: () {
              // Reset chat session
            },
          ),
        ],
      ),
      drawer: const VoiceFrontDrawer(), // Houses login, storefronts, and settings
      body: const ChatScreen(),         // Primary ChatGPT-style interface
    );
  }
}
```

---

## 3. Drawer Contents (`VoiceFrontDrawer`)
- **Header**: User account badge ("Tony Stark • Pro Plan")
- **Section 1: Storefronts**:
  - Active Storefronts (e.g., *Tony's Pizza*, *Urban Threads*)
  - Create New Storefront
- **Section 2: Developer / Intelligence**:
  - REA Component Library Stats (70+ components)
  - Pipeline Tracer (L1–L5 metrics)
- **Section 3: Account**:
  - Login / Logout details
  - API Keys & Settings
