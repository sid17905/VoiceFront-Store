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
  String? _errorText;

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
    _errorText = null;
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
    // Show user's chip selection as a transcript entry (display only, never mutate spec).
    setState(() {
      _messages.add(ChatMessage(text: '[${action.label}]', isUser: true));
    });
    _dispatchIntent(action.op, action.value);
  }

  void _dispatchIntent(String op, String value) {
    if (_currentSpec == null) return;
    final updated = Map<String, dynamic>.from(_currentSpec!);
    switch (op) {
      case 'set_hours':
        updated['hours'] = [value];
        break;
      case 'set_theme':
        updated['theme'] = value;
        break;
      case 'add_banner':
        updated['banner'] = value;
        break;
    }
    _currentSpec = updated;
    setState(() {
      _messages.add(ChatMessage(text: 'Updated **${op.replaceAll('_', ' ')}** ✓', isUser: false));
    });
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
      _errorText = null;
    });
    _scrollToBottom();

    try {
      // Stage 0 — Understanding
      await Future.delayed(const Duration(milliseconds: 600));
      if (_stopped) return;

      Map<String, dynamic> spec;
      if (_currentSpec != null &&
          RegExp(r'\b(change|update|add|remove|set)\b', caseSensitive: false).hasMatch(text)) {
        spec = Map<String, dynamic>.from(_currentSpec!);
      } else {
        final nlpResult = await VoiceFrontBackendService.extractStorefront(text);
        spec = Map<String, dynamic>.from(nlpResult['storefront_spec'] as Map? ?? {});
      }
      if (_stopped) return;

      // Stage 1 — Designing
      setState(() => _stageIndex = 1);
      await Future.delayed(const Duration(milliseconds: 600));
      if (_stopped) return;

      final category = spec['category'] as String? ?? 'services';
      final layoutResult = await VoiceFrontBackendService.generateLayout(spec, category);
      final html = layoutResult['html'] as String? ?? '';
      if (_stopped) return;

      // Stage 2 — Checking
      setState(() => _stageIndex = 2);
      await Future.delayed(const Duration(milliseconds: 400));
      if (_stopped) return;

      _currentSpec = spec;
      final shopName = spec['shop_name'] as String? ?? 'Your Store';
      final source = spec['source'] as String? ?? 'groq';
      AccountManager.addArtifact(shopName, category);

      final isOffline = source == 'fallback';

      setState(() {
        _isLoading = false;
        _stageIndex = 0;
        _messages.add(ChatMessage(
          text: isOffline
              ? 'Built **$shopName** using offline heuristics.\n\n> Connect the AI backend for richer results.'
              : 'Built **$shopName** — looking good! Here are some customisations:',
          isUser: false,
          type: MessageType.result,
          htmlPreview: html,
          storefrontSpec: spec,
          qaViolations: 0,
          actions: const [
            QuickAction(label: 'Add operating hours', op: 'set_hours', value: 'Mon–Sat: 9 AM – 9 PM'),
            QuickAction(label: 'Change primary colors', op: 'set_theme', value: 'vibrant'),
            QuickAction(label: 'Add discount banner', op: 'add_banner', value: '10% off today!'),
          ],
        ));
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _stageIndex = 0;
        _errorText = e.toString();
        _messages.add(ChatMessage(
          text: 'Something went wrong. Tap **Retry** to try again.',
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
      ),
    ));
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
                  onPublish: () {},
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
          onPressed: () => _sendMessage(_controller.text.trim().isNotEmpty ? null : _messages.firstWhere((m) => m.isUser, orElse: () => _messages.last).text),
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
