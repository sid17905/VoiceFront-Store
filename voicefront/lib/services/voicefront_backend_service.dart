import 'dart:convert';
import 'package:http/http.dart' as http;

class VoiceFrontBackendService {
  static const String nlpBaseUrl = 'http://10.0.2.2:8002';
  static const String layoutBaseUrl = 'http://10.0.2.2:8003';

  static final _nameRe = RegExp(r'(?:called|named)\s+([A-Za-z0-9\s&\']+?)(?:\.|,|$|and|\n|in\b)', caseSensitive: false);
  static final _priceRe = RegExp(r'(?:for|at|costs?|price|rs\.?|inr)\s*(?:rs\.?|inr)?\s*(\d+(?:\.\d+)?)', caseSensitive: false);
  static final _cityRe = RegExp(r'\bin\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)', caseSensitive: false);

  static String _extractShopName(String prompt) {
    final m = _nameRe.firstMatch(prompt);
    if (m != null) return m.group(1)!.trim();
    final words = prompt.trim().split(RegExp(r'\s+'));
    if (words.length >= 2) return '${words[0]} ${words[1]}';
    return 'My Store';
  }

  static double _extractPrice(String prompt) {
    final m = _priceRe.firstMatch(prompt);
    if (m != null) return double.tryParse(m.group(1)!) ?? 499;
    return 499;
  }

  static String _extractCity(String prompt) {
    final m = _cityRe.firstMatch(prompt);
    return m?.group(1)?.trim() ?? '';
  }

  static String _detectCategory(String prompt) {
    final lower = prompt.toLowerCase();
    if (RegExp(r'food|restaurant|cafe|coffee|bakery|pizza|biryani|kitchen|sweet').hasMatch(lower)) return 'food';
    if (RegExp(r'cloth|apparel|wear|shirt|dress|boutique|fashion|saree').hasMatch(lower)) return 'apparel';
    if (RegExp(r'electronic|mobile|laptop|phone|gadget|charger|tv').hasMatch(lower)) return 'electronics';
    if (RegExp(r'pharma|chemist|medicine|drug|healthcare|medical|clinic').hasMatch(lower)) return 'pharmacy';
    return 'services';
  }

  static String _detectProductName(String prompt, String category) {
    final lower = prompt.toLowerCase();
    if (lower.contains('training')) return 'Personal Training';
    if (lower.contains('coffee') || lower.contains('cappuccino')) return 'Cappuccino';
    if (lower.contains('guitar')) return 'Guitar Lessons';
    if (lower.contains('pizza')) return 'Signature Pizza';
    if (category == 'food') return 'Chef\'s Special';
    if (category == 'apparel') return 'Designer Collection';
    if (category == 'electronics') return 'Tech Service';
    if (category == 'pharmacy') return 'Health Consultation';
    return 'Premium Service';
  }

  static Future<Map<String, dynamic>> extractStorefront(String prompt) async {
    try {
      final response = await http.post(
        Uri.parse('$nlpBaseUrl/v1/nlp/extract'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'prompt': prompt}),
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      // fall through to client-side heuristic
    }

    final shopName = _extractShopName(prompt);
    final category = _detectCategory(prompt);
    final price = _extractPrice(prompt);
    final city = _extractCity(prompt);
    final productName = _detectProductName(prompt, category);

    return {
      "is_valid": true,
      "storefront_spec": {
        "shop_name": shopName,
        "category": category,
        "description": "$shopName — Quality $category in ${city.isNotEmpty ? city : 'your area'}",
        "products": [
          {"name": productName, "price": price, "currency": "INR", "description": "$productName at $shopName", "is_suggested": true}
        ],
        "contact": {"whatsapp": "9876543210"},
        "location": city.isNotEmpty ? {"city": city} : null,
        "source": "fallback"
      }
    };
  }

  static Future<Map<String, dynamic>> generateLayout(Map<String, dynamic> storefrontSpec, String category) async {
    try {
      final payload = Map<String, dynamic>.from(storefrontSpec);
      payload['category'] = category;
      final response = await http.post(
        Uri.parse('$layoutBaseUrl/v1/layout/generate'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      // fall through to client-side fallback
    }

    final shopName = storefrontSpec['shop_name'] ?? 'Store';
    final desc = storefrontSpec['description'] ?? '';
    final products = storefrontSpec['products'] as List? ?? [];
    final prodName = products.isNotEmpty ? products[0]['name'] : 'Service';
    final prodPrice = products.isNotEmpty ? products[0]['price'] : 499;
    final prodDesc = products.isNotEmpty ? (products[0]['description'] ?? '$prodName at $shopName') : '$prodName at $shopName';
    final whatsapp = storefrontSpec['contact']?['whatsapp'] ?? '9876543210';
    final waText = Uri.encodeComponent('Hi $shopName, I am interested in $prodName.');

    return {
      "template_id": category,
      "html": """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>$shopName</title><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet"><style>:root{--primary:#2A3A8A;--primary-dark:#1e2d6d;--accent:#4f6ef7;--surface:#f8fafc;--ink:#1e293b;--muted:#94a3b8;}*{box-sizing:border-box;margin:0;padding:0;}body{font-family:'Inter',system-ui,sans-serif;color:var(--ink);background:var(--surface);line-height:1.6;}header{background:linear-gradient(135deg,var(--primary),var(--primary-dark));color:#fff;padding:48px 24px;text-align:center;}h1{font-size:clamp(1.5rem,4vw,2.25rem);font-weight:700;margin-bottom:8px;}p.tagline{font-size:1rem;opacity:.9;max-width:560px;margin:0 auto;}.container{max-width:800px;margin:32px auto;padding:0 16px;}.card{background:#fff;padding:24px;border-radius:14px;box-shadow:0 4px 12px rgba(0,0,0,.06);display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;min-height:48px;}.card h3{font-size:1rem;font-weight:600;}.card .desc{font-size:.85rem;color:var(--muted);margin-top:4px;}.price{font-size:1.15rem;font-weight:700;color:var(--accent);background:var(--surface);padding:6px 14px;border-radius:8px;}.cta-row{text-align:center;margin:32px 0;display:flex;gap:12px;justify-content:center;flex-wrap:wrap;}.btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:14px 24px;border-radius:12px;font-weight:700;font-size:.95rem;text-decoration:none;}.btn-wa{background:#25D366;color:#fff;box-shadow:0 4px 14px rgba(37,211,102,.35);}.btn-call{background:var(--primary);color:#fff;}footer{text-align:center;padding:24px 16px;font-size:.75rem;color:var(--muted);border-top:1px solid #e2e8f0;margin-top:40px;}@media(max-width:480px){.card{flex-direction:column;align-items:flex-start;gap:12px;}.cta-row{flex-direction:column;}}</style></head><body><header><h1>$shopName</h1><p class="tagline">$desc</p></header><div class="container"><h2 style="font-size:1.1rem;font-weight:700;margin-bottom:16px;">Our Offerings</h2><div class="card"><div><h3>$prodName</h3><p class="desc">$prodDesc</p></div><span class="price">₹$prodPrice</span></div><div class="cta-row"><a href="https://wa.me/$whatsapp?text=$waText" class="btn btn-wa" target="_blank" rel="noopener">WhatsApp to Book</a><a href="tel:$whatsapp" class="btn btn-call">Call Now</a></div></div><footer>$shopName &bull; Powered by VoiceFront</footer></body></html>"""
    };
  }
}
