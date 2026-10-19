import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart' show debugPrint;
import 'package:http/http.dart' as http;

/// Thrown when a backend call fails. The UI must show this rather than
/// silently substituting invented content.
class BackendException implements Exception {
  final String message;
  final int? statusCode;
  BackendException(this.message, [this.statusCode]);

  @override
  String toString() => statusCode == null ? message : '$message (HTTP $statusCode)';
}

class VoiceFrontBackendService {
  /// Host is injectable so a physical device or another machine can be used:
  ///   flutter run --dart-define=API_HOST=192.168.1.5
  /// Defaults to the Android emulator's alias for the host loopback.
  static const String _host = String.fromEnvironment('API_HOST', defaultValue: '10.0.2.2');

  static const String nlpBaseUrl = 'http://$_host:8002';
  static const String layoutBaseUrl = 'http://$_host:8003';
  static const String qaBaseUrl = 'http://$_host:8004';
  static const String publishBaseUrl = 'http://$_host:8005';

  static const Duration _nlpTimeout = Duration(seconds: 30);
  static const Duration _layoutTimeout = Duration(seconds: 30);
  static const Duration _qaTimeout = Duration(seconds: 120);

  static final _nameRe = RegExp(r"(?:called|named)\s+([A-Za-z0-9\s&']+?)(?:\.|,|$|and|\n|in\b)",
      caseSensitive: false);
  static final _priceRe = RegExp(
      r'(?:for|at|costs?|price|rs\.?|inr)\s*(?:rs\.?|inr)?\s*(\d+(?:\.\d+)?)',
      caseSensitive: false);
  static final _cityRe = RegExp(r'\bin\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)', caseSensitive: false);

  static Future<Map<String, dynamic>> _postJson(
    String url,
    Map<String, dynamic> body,
    Duration timeout,
  ) async {
    final response = await http
        .post(
          Uri.parse(url),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(timeout);

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw BackendException('Request failed: ${response.body}', response.statusCode);
  }

  /// Calls NLP. Throws BackendException on failure — there is no client-side
  /// guess. The previous implementation fabricated a shop name, price and phone
  /// number whenever the backend was unreachable, which produced pages that
  /// looked real but contained invented data.
  static Future<Map<String, dynamic>> extractStorefront(String prompt) async {
    final json = await _postJson(
      '$nlpBaseUrl/v1/nlp/extract',
      {'prompt': prompt},
      _nlpTimeout,
    );
    final spec = json['storefront_spec'];
    if (spec is! Map<String, dynamic>) {
      throw BackendException('Malformed NLP response');
    }
    return json;
  }

  static dynamic _stripNulls(dynamic v) {
    if (v is Map) {
      return {for (final e in v.entries) if (e.value != null) e.key: _stripNulls(e.value)};
    }
    if (v is List) return v.map(_stripNulls).toList();
    return v;
  }

  static Future<Map<String, dynamic>> generateLayout(
    Map<String, dynamic> storefrontSpec,
    String category,
  ) async {
    final payload = Map<String, dynamic>.from(_stripNulls(storefrontSpec) as Map);
    payload['category'] = category;
    final json = await _postJson(
      '$layoutBaseUrl/v1/layout/generate',
      payload,
      _layoutTimeout,
    );
    if (json['html'] is! String) {
      throw BackendException('Malformed layout response');
    }
    return json;
  }

  /// Runs QA against the generated HTML. Returns the qa_report map.
  static Future<Map<String, dynamic>> runQa(String html) async {
    final json = await _postJson(
      '$qaBaseUrl/v1/qa/run',
      {'html': html, 'auto_repair': false},
      _qaTimeout,
    );
    final report = json['qa_report'];
    if (report is! Map<String, dynamic>) {
      throw BackendException('Malformed QA response');
    }
    return report;
  }

  /// Publishes a previously rendered bundle. Returns the live URL.
  static Future<String> publish(String versionId, {String? apiKey}) async {
    final response = await http
        .post(
          Uri.parse('$publishBaseUrl/v1/publish'),
          headers: {
            'Content-Type': 'application/json',
            if (apiKey != null && apiKey.isNotEmpty) 'X-API-Key': apiKey,
          },
          body: jsonEncode({'version_id': versionId}),
        )
        .timeout(_layoutTimeout);

    if (response.statusCode == 200) {
      return (jsonDecode(response.body) as Map<String, dynamic>)['live_url'] as String;
    }
    throw BackendException('Publish failed', response.statusCode);
  }

  // --- Offline heuristics retained for tests and for the sample-prompt UI. ---
  // They are NOT used to substitute for a failed backend call.

  static String extractShopName(String prompt) {
    final m = _nameRe.firstMatch(prompt);
    if (m != null) return m.group(1)!.trim();
    final words = prompt.trim().split(RegExp(r'\s+'));
    if (words.length >= 2) return '${words[0]} ${words[1]}';
    return 'My Store';
  }

  static double? extractPrice(String prompt) {
    final m = _priceRe.firstMatch(prompt);
    return m == null ? null : double.tryParse(m.group(1)!);
  }

  static String extractCity(String prompt) => _cityRe.firstMatch(prompt)?.group(1)?.trim() ?? '';

  static String detectCategory(String prompt) {
    final lower = prompt.toLowerCase();
    if (RegExp(r'food|restaurant|cafe|coffee|bakery|pizza|biryani|kitchen|sweet').hasMatch(lower)) {
      return 'food';
    }
    if (RegExp(r'cloth|apparel|wear|shirt|dress|boutique|fashion|saree').hasMatch(lower)) {
      return 'apparel';
    }
    if (RegExp(r'electronic|mobile|laptop|phone|gadget|charger|tv').hasMatch(lower)) {
      return 'electronics';
    }
    if (RegExp(r'pharma|chemist|medicine|drug|healthcare|medical|clinic').hasMatch(lower)) {
      return 'pharmacy';
    }
    return 'services';
  }

  static void logFailure(Object error) => debugPrint('VoiceFront backend: $error');
}
