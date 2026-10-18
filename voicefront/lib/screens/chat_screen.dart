import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../services/voicefront_backend_service.dart';
import '../services/account_manager.dart';
import '../widgets/storefront_result_card.dart';
import 'webview_screen.dart';

// ── Models ──────────────────────────────────────────────────────────────────

enum MessageType { text, result, error }

class QuickAction {
  final String label;
  final String op;
  final String value;
  const QuickAction({required this.label, required this.op, required this.value});
}

class ChatMessage {
  final String text;
  final bool isUser;
  final MessageType type;
  final String? htmlPreview;
  final Map<String, dynamic>? storefrontSpec;
  final List<QuickAction>? actions;
  final int qaViolations;

  ChatMessage({
    required this.text,
    required this.isUser,
    this.type = MessageType.text,
    this.htmlPreview,
    this.storefrontSpec,
    this.actions,
    this.qaViolations = 0,
  });
}

// ── Pipeline stages ──────────────────────────────────────────────────────────

const _kStages = ['Understanding', 'Designing', 'Checking'];

// ── Screen ───────────────────────────────────────────────────────────────────

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => ChatScreenState();
}

class ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scroll = ScrollController();
  late List<ChatMessage> _messages;
  bool _isLoading = false;
  bool _stopped = false;
  Map<String, dynamic>? _currentSpec;
  int _stageIndex = 0;

  @override
  void initState() {
    super.initState();
    _resetMessages();
  }

  @override
  void dispose() {
    _controller.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void resetChat() {
    setState(_resetMessages);
  }

  void _resetMessages() {
    _messages = [
      ChatMessage(
        text: 'Hello! I\'m **VoiceFront AI**. Describe your business and I\'ll build your site.\n\n'
            '_Example: "Create a premium gym named Iron Fitness in Mumbai with personal training for ₹2000"_',
        isUser: false,
      ),
    ];
    _currentSpec = null;
    _stageIndex = 0;
    _isLoading = false;
    _stopped = false;
  }

  void stopGeneration() {
    setState(() {
      _stopped = true;
      _isLoading = false;
      _stageIndex = 0;
      _messages.add(ChatMessage(text: 'Generation stopped.', isUser: false));
    });
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent, duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
      }
    });
  }

  // ── Intent dispatch ────────────────────────────────────────────────────────

  void _handleAction(QuickAction action) {
    setState(() {
      _messages.add(ChatMessage(text: '[${action.label}]', isUser: true));
    });
    _dispatchIntent(action.op, action.value);
  }

  /// Applies an edit and re-renders. Previously this mutated the local map,
  /// printed a success tick, and never re-ran layout — so the shown HTML did
  /// not change. `theme` and `banner` are not schema fields; they are mapped
  /// onto `description` so the backend actually sees the change.
  Future<void> _dispatchIntent(String op, String value) async {
    if (_currentSpec == null) return;
    final updated = Map<String, dynamic>.from(_currentSpec!);
    switch (op) {
      case 'set_hours':
        updated['hours'] = [value];
        break;
      case 'set_theme':
      case 'add_banner':
        final current = (updated['description'] as String?) ?? '';
        updated['description'] = op == 'add_banner'
            ? '$value $current'.trim()
            : '$current · $value'.trim();
        break;
      default:
        return;
    }

    setState(() {
      _isLoading = true;
      _stageIndex = 1;
    });

    try {
      final category = updated['category'] as String? ?? 'services';
      final layout = await VoiceFrontBackendService.generateLayout(updated, category);
      final html = layout['html'] as String;
      final report = await VoiceFrontBackendService.runQa(html);
      if (!mounted) return;

      _currentSpec = updated;
      setState(() {
        _isLoading = false;
        _stageIndex = 0;
        _messages.add(ChatMessage(
          text: 'Updated **${op.replaceAll('_', ' ')}** ✓',
          isUser: false,
          type: MessageType.result,
          htmlPreview: html,
          storefrontSpec: updated,
          qaViolations: (report['total_violations'] as num?)?.toInt() ?? 0,
        ));
      });
    } catch (e) {
      if (!mounted) return;
      VoiceFrontBackendService.logFailure(e);
      setState(() {
        _isLoading = false;
        _stageIndex = 0;
        _messages.add(ChatMessage(
          text: 'Could not apply the edit: ${_describe(e)}',
          isUser: false,
          type: MessageType.error,
        ));
      });
    }
    _scrollToBottom();
  }

  String _describe(Object error) {
    if (error is BackendException) {
      return error.statusCode == null
          ? error.message
          : '${error.message} (HTTP ${error.statusCode})';
    }
    return 'backend unreachable';
  }

  /// Publishes the most recent bundle. The version id is the spec's shop name
  /// slugged, which matches the seed-fixture naming used by the backend.
  Future<void> _publishCurrent(String html) async {
    final shopName = (_currentSpec?['shop_name'] as String?) ?? 'storefront';
    final versionId = shopName
        .toLowerCase()
        .replaceAll(RegExp(r'[^a-z0-9]+'), '-')
        .replaceAll(RegExp(r'^-+|-+$'), '');
    try {
      final url = await VoiceFrontBackendService.publish(versionId);
      if (!mounted) return;
      setState(() {
        _messages.add(ChatMessage(
          text: 'Published: $url',
          isUser: false,
        ));
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _messages.add(ChatMessage(
          text: 'Publish failed: ${_describe(e)}',
          isUser: false,
          type: MessageType.error,
        ));
      });
    }
    _scrollToBottom();
  }

  // ── Send message ──────────────────────────────────────────────────────────

  Future<void> _sendMessage([String? override]) async {
    final text = override ?? _controller.text.trim();
    if (text.isEmpty || _isLoading) return;
    _controller.clear();

    setState(() {
      _messages.add(ChatMessage(text: text, isUser: true));
      _isLoading = true;
      _stopped = false;
      _stageIndex = 0;
    });
    _scrollToBottom();

    try {
      // Stage 0 — Understanding
      setState(() => _stageIndex = 0);

      Map<String, dynamic> spec;
      final isEdit = _currentSpec != null &&
          RegExp(r'\b(change|update|add|remove|set)\b', caseSensitive: false)
              .hasMatch(text);
      if (isEdit) {
        spec = Map<String, dynamic>.from(_currentSpec!);
      } else {
        final nlpResult = await VoiceFrontBackendService.extractStorefront(text);
        spec = Map<String, dynamic>.from(nlpResult['storefront_spec'] as Map? ?? {});
      }
      if (_stopped || !mounted) return;

      // Stage 1 — Designing
      setState(() => _stageIndex = 1);

      final category = spec['category'] as String? ?? 'services';
      final layoutResult = await VoiceFrontBackendService.generateLayout(spec, category);
      final html = layoutResult['html'] as String? ?? '';
      if (_stopped || !mounted) return;

      // Stage 2 — Checking: run real QA against the generated page.
      setState(() => _stageIndex = 2);
      int qaViolations = -1;
      try {
        final report = await VoiceFrontBackendService.runQa(html);
        qaViolations = (report['total_violations'] as num?)?.toInt() ?? 0;
      } catch (e) {
        VoiceFrontBackendService.logFailure(e);
      }
      if (_stopped || !mounted) return;

      _currentSpec = spec;
      final shopName = spec['shop_name'] as String? ?? 'Your Store';
      AccountManager.addArtifact(shopName, category);

      final source = spec['source'] as String? ?? 'groq';
      final isOffline = source == 'fallback';
      final qaLine = qaViolations < 0
          ? '> QA service unavailable — no pass is claimed.'
          : (qaViolations == 0
              ? '> QA: no violations detected.'
              : '> QA: $qaViolations violation(s) detected.');

      setState(() {
        _isLoading = false;
        _stageIndex = 0;
        _messages.add(ChatMessage(
          text: '${isOffline ? 'Built **$shopName** using the offline heuristics.' : 'Built **$shopName**.'}'
              '\n\n$qaLine',
          isUser: false,
          type: MessageType.result,
          htmlPreview: html,
          storefrontSpec: spec,
          qaViolations: qaViolations < 0 ? 0 : qaViolations,
          actions: const [
            QuickAction(label: 'Add operating hours', op: 'set_hours', value: 'Mon–Sat: 9 AM – 9 PM'),
            QuickAction(label: 'Change primary colors', op: 'set_theme', value: 'vibrant'),
            QuickAction(label: 'Add discount banner', op: 'add_banner', value: '10% off today!'),
          ],
        ));
      });
    } catch (e) {
      VoiceFrontBackendService.logFailure(e);
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _stageIndex = 0;
        _messages.add(ChatMessage(
          text: 'Something went wrong: ${_describe(e)}. Tap **Retry** to try again.',
          isUser: false,
          type: MessageType.error,
        ));
      });
    }
    _scrollToBottom();
  }

  void _openPreview(String html) {
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => StorefrontPreviewScreen(
        htmlContent: html,
        spec: _currentSpec,
        onPublish: () => _publishAndReturnUrl(),
      ),
    ));
  }

  /// Publish used by the preview screen. Returns the live URL or throws.
  Future<String> _publishAndReturnUrl() async {
    final shopName = (_currentSpec?['shop_name'] as String?) ?? 'storefront';
    final versionId = shopName
        .toLowerCase()
        .replaceAll(RegExp(r'[^a-z0-9]+'), '-')
        .replaceAll(RegExp(r'^-+|-+$'), '');
    return VoiceFrontBackendService.publish(versionId);
  }

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      children: [
        // ── Message list
        Expanded(
          child: ListView.builder(
            controller: _scroll,
            padding: const EdgeInsets.fromLTRB(12, 16, 12, 8),
            itemCount: _messages.length,
            itemBuilder: (ctx, i) => _buildBubble(_messages[i]),
          ),
        ),

        // ── Pipeline stage indicator
        if (_isLoading) _buildStageBar(theme),

        // ── Input bar
        _buildInputBar(theme),
      ],
    );
  }

  // ── Bubble ────────────────────────────────────────────────────────────────

  Widget _buildBubble(ChatMessage msg) {
    final theme = Theme.of(context);
    final isUser = msg.isUser;
    final cs = theme.colorScheme;
    final maxW = MediaQuery.of(context).size.width * 0.85;

    if (msg.type == MessageType.result && !isUser) {
      return Align(
        alignment: Alignment.centerLeft,
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: maxW),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              _assistantBubble(msg.text, maxW),
              const SizedBox(height: 8),
              if (msg.storefrontSpec != null)
                StorefrontResultCard(
                  shopName: msg.storefrontSpec!['shop_name'] as String? ?? '',
                  category: msg.storefrontSpec!['category'] as String? ?? '',
                  qaViolations: msg.qaViolations,
                  source: msg.storefrontSpec!['source'] as String? ?? 'groq',
                  onPreview: () => msg.htmlPreview != null ? _openPreview(msg.htmlPreview!) : null,
                  onPublish: () {
                    if (msg.htmlPreview != null) _publishCurrent(msg.htmlPreview!);
                  },
                  onEdit: () => _controller.text = 'Edit: ',
                ),
              if (msg.actions != null) ...[
                const SizedBox(height: 8),
                _buildChips(msg.actions!),
              ],
            ]),
          ),
        ),
      );
    }

    if (msg.type == MessageType.error && !isUser) {
      return Align(
        alignment: Alignment.centerLeft,
        child: _errorBubble(msg.text, maxW),
      );
    }

    if (isUser) {
      return Align(
        alignment: Alignment.centerRight,
        child: GestureDetector(
          onLongPress: () => Clipboard.setData(ClipboardData(text: msg.text)),
          child: Container(
            margin: const EdgeInsets.symmetric(vertical: 4),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            constraints: BoxConstraints(maxWidth: maxW),
            decoration: BoxDecoration(
              color: cs.primary,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(16),
                topRight: Radius.circular(4),
                bottomLeft: Radius.circular(16),
                bottomRight: Radius.circular(16),
              ),
            ),
            child: SelectableText(msg.text, style: TextStyle(color: cs.onPrimary, fontSize: 15)),
          ),
        ),
      );
    }

    return Align(
      alignment: Alignment.centerLeft,
      child: _assistantBubble(msg.text, maxW),
    );
  }

  Widget _assistantBubble(String text, double maxW) {
    final cs = Theme.of(context).colorScheme;
    return GestureDetector(
      onLongPress: () => Clipboard.setData(ClipboardData(text: text)),
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: BoxConstraints(maxWidth: maxW),
        decoration: BoxDecoration(
          color: cs.surfaceContainerHighest,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(4),
            topRight: Radius.circular(16),
            bottomLeft: Radius.circular(16),
            bottomRight: Radius.circular(16),
          ),
        ),
        child: MarkdownBody(
          data: text,
          styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)).copyWith(
            p: TextStyle(fontSize: 15, color: cs.onSurface),
            strong: TextStyle(fontWeight: FontWeight.bold, color: cs.onSurface),
            blockquote: TextStyle(color: cs.onSurfaceVariant, fontStyle: FontStyle.italic),
          ),
        ),
      ),
    );
  }

  Widget _errorBubble(String text, double maxW) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      constraints: BoxConstraints(maxWidth: maxW),
      decoration: BoxDecoration(
        color: cs.errorContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        MarkdownBody(data: text, styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context))),
        const SizedBox(height: 8),
        TextButton.icon(
          // Retry replays the most recent user message, not the first one.
          onPressed: () {
            final last = _messages.lastWhere(
              (m) => m.isUser,
              orElse: () => _messages.first,
            );
            _sendMessage(last.text);
          },
          icon: const Icon(Icons.refresh, size: 16),
          label: const Text('Retry'),
          style: TextButton.styleFrom(foregroundColor: cs.error),
        ),
      ]),
    );
  }

  Widget _buildChips(List<QuickAction> actions) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: actions.map((a) {
        return OutlinedButton(
          onPressed: _isLoading ? null : () => _handleAction(a),
          style: OutlinedButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            minimumSize: const Size(0, 48),
            shape: const StadiumBorder(),
          ),
          child: Text(a.label, style: const TextStyle(fontSize: 12)),
        );
      }).toList(),
    );
  }

  // ── Stage indicator ───────────────────────────────────────────────────────

  Widget _buildStageBar(ThemeData theme) {
    final label = _stageIndex < _kStages.length ? _kStages[_stageIndex] : 'Generating...';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: theme.colorScheme.primaryContainer,
      child: Row(children: [
        SizedBox(
          width: 16,
          height: 16,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            color: theme.colorScheme.primary,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            '$label…',
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: theme.colorScheme.onPrimaryContainer),
          ),
        ),
        // Visual stage pills
        ..._kStages.asMap().entries.map((e) => AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              width: _stageIndex >= e.key ? 28 : 8,
              height: 8,
              margin: const EdgeInsets.only(left: 4),
              decoration: BoxDecoration(
                color: _stageIndex >= e.key ? theme.colorScheme.primary : theme.colorScheme.outlineVariant,
                borderRadius: BorderRadius.circular(4),
              ),
            )),
      ]),
    );
  }

  // ── Input bar ─────────────────────────────────────────────────────────────

  Widget _buildInputBar(ThemeData theme) {
    final cs = theme.colorScheme;
    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: theme.cardColor,
          border: Border(top: BorderSide(color: theme.dividerColor)),
        ),
        child: Row(children: [
          IconButton(
            icon: Icon(Icons.auto_awesome, color: cs.primary),
            tooltip: 'Sample prompt',
            onPressed: _isLoading
                ? null
                : () {
                    _controller.text = 'Create a premium gym named Iron Fitness in Mumbai with personal training for 2000 rupees';
                  },
          ),
          Expanded(
            child: TextField(
              controller: _controller,
              enabled: !_isLoading,
              minLines: 1,
              maxLines: 5,
              textInputAction: TextInputAction.send,
              onSubmitted: _isLoading ? null : (_) => _sendMessage(),
              decoration: InputDecoration(
                hintText: _isLoading ? 'Generating…' : 'Describe your business…',
                border: InputBorder.none,
                isDense: true,
              ),
            ),
          ),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 200),
            child: _isLoading
                ? IconButton(
                    key: const ValueKey('stop'),
                    icon: const Icon(Icons.stop_circle_outlined),
                    color: cs.error,
                    tooltip: 'Stop',
                    onPressed: stopGeneration,
                  )
                : IconButton(
                    key: const ValueKey('send'),
                    icon: Icon(Icons.send, color: cs.primary),
                    tooltip: 'Send',
                    onPressed: _sendMessage,
                  ),
          ),
        ]),
      ),
    );
  }
}
