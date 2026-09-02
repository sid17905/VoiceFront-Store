import 'dart:convert';
import 'package:http/http.dart' as http;

class GroqApiService {
  // Using a provided demo key or a publicly available fallback model if necessary.
  static const String _apiKey = 'gsk_YOUR_GROQ_API_KEY_HERE'; // Replace with a valid key for real deployment
  static const String _asrUrl = 'https://api.groq.com/openai/v1/audio/transcriptions';

  static Future<String> transcribeAudio(String filePath, String language) async {
    // Note: Due to Flutter limits in a demo environment without a real API key,
    // we use a simulated response if actual API call fails or isn't configured.
    if (_apiKey == 'gsk_YOUR_GROQ_API_KEY_HERE') {
      await Future.delayed(const Duration(seconds: 2));
      if (language == 'hi') {
        return "मैं जयपुर में कृष्णा स्वीट्स नाम की दुकान खोलना चाहता हूं। हम दूध के उत्पाद और समोसे बेचते हैं। मुझे सुबह 8 बजे से रात 9 बजे तक खुला रहना है और लोग मुझे व्हाट्सएप 9876543210 पर संपर्क कर सकते हैं।";
      }
      return "I want to open a shop called Krishna Sweets for selling milk products and samosas in Jaipur. I need to be open from 8 AM to 9 PM and people can contact me on WhatsApp 9876543210.";
    }

    try {
      var request = http.MultipartRequest('POST', Uri.parse(_asrUrl));
      request.headers.addAll({
        'Authorization': 'Bearer $_apiKey',
      });
      request.fields['model'] = 'whisper-large-v3';
      if (language != 'auto') {
        request.fields['language'] = language;
      }
      request.files.add(await http.MultipartFile.fromPath('file', filePath));

      var response = await request.send();
      var responseData = await response.stream.bytesToString();
      if (response.statusCode == 200) {
        var json = jsonDecode(responseData);
        return json['text'] ?? '';
      }
    } catch (e) {
      print('Groq API Error: $e');
    }
    return '';
  }
}
