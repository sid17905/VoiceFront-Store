import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:webview_flutter/webview_flutter.dart';

import '../services/voicefront_backend_service.dart';

class StorefrontPreviewScreen extends StatefulWidget {
  final String htmlContent;
  final Map<String, dynamic>? spec;
  final Future<String> Function()? onPublish;

  const StorefrontPreviewScreen({
    super.key,
    required this.htmlContent,
    this.spec,
    this.onPublish,
  });

  @override
  State<StorefrontPreviewScreen> createState() => _StorefrontPreviewScreenState();
}

class _StorefrontPreviewScreenState extends State<StorefrontPreviewScreen> {
  late final WebViewController _controller;
  bool _loading = true;
  bool _hasError = false;
  bool _desktopMode = false;
  bool _publishing = false;

  /// Publishes through the callback supplied by the caller. Previously this
  /// button had an empty onPressed, so the product's primary action did
  /// nothing at all.
  Future<void> _publish() async {
    final callback = widget.onPublish;
    if (callback == null) {
      _showMessage('Publish is not available in preview mode.');
      return;
    }
    setState(() => _publishing = true);
    try {
      final url = await callback();
      if (!mounted) return;
      _showMessage('Published: $url');
    } catch (error) {
      if (!mounted) return;
      final detail = error is BackendException ? error.toString() : 'backend unreachable';
      _showMessage('Publish failed: $detail');
    } finally {
      if (mounted) setState(() => _publishing = false);
    }
  }

  void _showMessage(String text) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
  }

  @override
  void initState() {
    super.initState();
    _initWebView();
  }

  void _initWebView() {
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(NavigationDelegate(
        onPageStarted: (_) => setState(() => _loading = true),
        onPageFinished: (_) => setState(() => _loading = false),
        onWebResourceError: (_) => setState(() {
          _loading = false;
          _hasError = true;
        }),
        onNavigationRequest: (req) {
          final url = req.url;
          if (url.contains('wa.me') || url.startsWith('tel:')) {
            return NavigationDecision.navigate;
          }
          return NavigationDecision.prevent;
        },
      ))
      ..loadHtmlString(_viewportWrapped(widget.htmlContent));
  }

  String _viewportWrapped(String html) {
    if (_desktopMode && !html.contains('width=1440')) {
      return html.replaceFirst(
        'width=device-width',
        'width=1440',
      );
    }
    return html;
  }

  void _toggleViewport() {
    setState(() {
      _desktopMode = !_desktopMode;
      _hasError = false;
      _loading = true;
    });
    _controller.loadHtmlString(_viewportWrapped(widget.htmlContent));
  }

  void _retry() {
    setState(() {
      _hasError = false;
      _loading = true;
    });
    _controller.loadHtmlString(_viewportWrapped(widget.htmlContent));
  }

  void _share() {
    final name = widget.spec?['shop_name'] ?? 'My Store';
    Clipboard.setData(ClipboardData(text: 'Check out $name — built with VoiceFront AI'));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Link copied to clipboard')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final cs = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        leading: const BackButton(),
        title: Text(
          widget.spec?['shop_name'] ?? 'Preview',
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: Icon(_desktopMode ? Icons.phone_android : Icons.desktop_mac_outlined, size: 20),
            tooltip: _desktopMode ? 'Mobile view' : 'Desktop view',
            onPressed: _toggleViewport,
          ),
          IconButton(
            icon: const Icon(Icons.share_outlined, size: 20),
            tooltip: 'Share',
            onPressed: _share,
          ),
          TextButton(
            onPressed: _publishing ? null : _publish,
            child: _publishing
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Text('Publish',
                    style: TextStyle(fontWeight: FontWeight.bold, color: cs.primary)),
          ),
        ],
      ),
      body: Stack(
        children: [
          if (!_hasError) WebViewWidget(controller: _controller),
          if (_loading && !_hasError)
            Container(
              color: cs.surface.withValues(alpha: 0.85),
              child: Center(
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  CircularProgressIndicator(color: cs.primary),
                  const SizedBox(height: 16),
                  Text('Rendering preview…', style: TextStyle(color: cs.onSurface)),
                ]),
              ),
            ),
          if (_hasError)
            Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Icon(Icons.error_outline, size: 48, color: cs.error),
                const SizedBox(height: 12),
                Text('Failed to load preview', style: TextStyle(color: cs.onSurface, fontSize: 16)),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: _retry,
                  icon: const Icon(Icons.refresh, size: 16),
                  label: const Text('Retry'),
                ),
              ]),
            ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.of(context).pop(),
        icon: const Icon(Icons.chat_outlined),
        label: const Text('Edit via chat'),
        backgroundColor: cs.secondaryContainer,
        foregroundColor: cs.onSecondaryContainer,
      ),
    );
  }
}
