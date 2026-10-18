# VoiceFront-Store V2: Unified Background Engine & Live In-App Preview Strategy

## 1. Unified Background Daemon / Server Architecture
To achieve a fluid ChatGPT-like experience where background processes (NLP extraction, REA component scraping, layout synthesis, QA auditing) run asynchronously without blocking the user interface, we consolidate and run our microservices as a persistent background daemon mesh communicating via JSON APIs and WebSockets.

### The Background Worker Mesh (`infra/docker/docker-compose.dev.yml` expansion)
- **API Gateway / Orchestrator**: Manages WebSocket connections for real-time streaming chat events.
- **Background Task Queue (Celery / Redis / FastAPI Async BackgroundTasks)**:
  - Task 1: `process_user_prompt` (Calls NLP → Layout → QA asynchronously).
  - Task 2: `rea_scrape_worker` (Background scraping and component library harvesting).

---

## 2. In-App Live Website Preview Strategy (Before Deployment)

Since mobile and web users need to inspect and interact with the storefront *before* pushing to AWS S3 / CloudFront production, we implement a **Local Sandbox Preview Renderer**:

### How It Works:
1. **HTML/CSS Bundle Generation**: `layout-service` generates the complete self-contained HTML/CSS/JS string.
2. **In-App WebView Rendering**:
   - In Flutter (`voicefront/`), we use `webview_flutter` or `flutter_html`.
   - Instead of loading a remote URL, the WebView directly loads the raw HTML string via `controller.loadHtmlString(htmlContent)`.
3. **Interactive Sandbox**:
   - Users can test buttons (e.g., WhatsApp click-to-chat links, product grids, scrolling) instantly inside the chat preview container.
4. **Publish Trigger**:
   - Once the user is satisfied with the live preview, tapping **"Publish Storefront"** triggers the background publish worker to upload to S3 and issue the production URL.

---

## 3. Implementation Blueprint

### A. WebView Preview Widget (`voicefront/lib/widgets/storefront_preview_pane.dart`)
```dart
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

class StorefrontPreviewPane extends StatefulWidget {
  final String htmlContent;
  const StorefrontPreviewPane({Key? key, required this.htmlContent}) : super(key: key);

  @override
  State<StorefrontPreviewPane> createState() => _StorefrontPreviewPaneState();
}

class _StorefrontPreviewPaneState extends State<StorefrontPreviewPane> {
  late final WebViewController _controller;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..loadHtmlString(widget.htmlContent);
  }

  @override
  void didUpdateWidget(covariant StorefrontPreviewPane oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.htmlContent != widget.htmlContent) {
      _controller.loadHtmlString(widget.htmlContent);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade300),
        borderRadius: BorderRadius.circular(12),
      ),
      clipBehavior: Clip.antiAlias,
      child: WebViewWidget(controller: _controller),
    );
  }
}
```

### B. Background Execution Flow
- User types prompt in chat.
- Background worker executes NLP extraction, layout compilation, and QA check.
- WebSocket emits `preview_ready` event carrying the HTML string.
- App updates the WebView pane live while assistant replies in chat.
