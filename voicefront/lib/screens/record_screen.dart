import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import '../theme/app_colors.dart';
import '../services/groq_api_service.dart';

class RecordScreen extends StatefulWidget {
  final VoidCallback onNavigateToReview;

  const RecordScreen({super.key, required this.onNavigateToReview});

  @override
  State<RecordScreen> createState() => _RecordScreenState();
}

class _RecordScreenState extends State<RecordScreen>
    with SingleTickerProviderStateMixin {
  bool _isRecording = false;
  String _selectedLanguage = 'en'; // 'en' or 'hi'
  String _liveTranscript = '';
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;
  final FlutterTts _flutterTts = FlutterTts();

  // Mock voice samples for reliable demonstration
  final Map<String, List<String>> _sampleUtterances = {
    'en': [
      "I want to open a shop called Krishna Sweets for selling milk products and samosas in Jaipur. I need to be open from 8 AM to 9 PM and people can contact me on WhatsApp 9876543210.",
      "Hello, I am setting up Rahul Electronics in Pune. We sell smart watches, power banks, and mobile covers. WhatsApp us at 9123456789.",
    ],
    'hi': [
      "मैं जयपुर में कृष्णा स्वीट्स नाम की दुकान खोलना चाहता हूं। हम दूध के उत्पाद और समोसे बेचते हैं। संपर्क नंबर 9876543210 है।",
      "नमस्ते, मैं शर्मा जनरल स्टोर शुरू कर रहा हूं। हम चावल, दाल और तेल बेचते हैं। सुबह 9 से शाम 8 बजे तक खुला रहेगा।",
    ]
  };

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.2).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    _initTts();
  }

  void _initTts() async {
    await _flutterTts.setVolume(1.0);
    await _flutterTts.setPitch(1.0);
  }

  void _speakFeedback(String text) async {
    await _flutterTts.setLanguage(_selectedLanguage == 'hi' ? 'hi-IN' : 'en-US');
    await _flutterTts.speak(text);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _flutterTts.stop();
    super.dispose();
  }

  void _toggleRecording() {
    setState(() {
      _isRecording = !_isRecording;
    });

    if (_isRecording) {
      _pulseController.repeat(reverse: true);
      _startSimulatedStream();
    } else {
      _pulseController.stop();
    }
  }

  void _startSimulatedStream() async {
    List<String> samples = _sampleUtterances[_selectedLanguage]!;
    String fullText = samples[0];
    List<String> words = fullText.split(' ');

    _liveTranscript = '';
    for (int i = 0; i < words.length; i++) {
      if (!_isRecording) break;
      await Future.delayed(const Duration(milliseconds: 150));
      if (mounted) {
        setState(() {
          _liveTranscript += (i == 0 ? '' : ' ') + words[i];
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('VoiceFront Studio'),
        actions: [
          _buildLanguageSelector(),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 12),
            _buildStatusBadge(),
            const SizedBox(height: 16),
            _buildPresetsRow(),
            const SizedBox(height: 16),
            Expanded(
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 24),
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppColors.cardBg,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.grey.withValues(alpha: 0.2)),
                ),
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            _selectedLanguage == 'hi' ? 'रीयल-टाइम प्रतिलेखन' : 'Live Transcript Stream',
                            style: const TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.bold,
                              color: AppColors.textSecondary,
                            ),
                          ),
                          if (_liveTranscript.isNotEmpty)
                            IconButton(
                              icon: const Icon(Icons.volume_up, size: 20, color: AppColors.brandBlue),
                              onPressed: () => _speakFeedback(_liveTranscript),
                            )
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(
                        _liveTranscript.isEmpty
                            ? (_selectedLanguage == 'hi' 
                                ? 'बोलना शुरू करने के लिए माइक दबाएं...' 
                                : 'Tap the microphone to speak, or pick a sample above...')
                            : _liveTranscript,
                        style: TextStyle(
                          fontSize: 16,
                          height: 1.5,
                          fontStyle: _liveTranscript.isEmpty ? FontStyle.italic : FontStyle.normal,
                          color: _liveTranscript.isEmpty ? AppColors.textSecondary : AppColors.textPrimary,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
            _buildMicButton(),
            const SizedBox(height: 20),
            _buildStopButton(),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildLanguageSelector() {
    return Padding(
      padding: const EdgeInsets.only(right: 16),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: _selectedLanguage,
          icon: const Icon(Icons.language, color: AppColors.brandBlue),
          items: const [
            DropdownMenuItem(value: 'en', child: Text('English (EN)')),
            DropdownMenuItem(value: 'hi', child: Text('हिंदी (HI)')),
          ],
          onChanged: (val) {
            if (val != null) {
              setState(() {
                _selectedLanguage = val;
                _liveTranscript = '';
              });
            }
          },
        ),
      ),
    );
  }

  Widget _buildPresetsRow() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Row(
        children: [
          ActionChip(
            avatar: const Icon(Icons.play_circle_fill, size: 16, color: AppColors.forestGreen),
            label: Text(_selectedLanguage == 'hi' ? 'नमूना 1: कृष्णा स्वीट्स' : 'Sample: Sweet Shop'),
            onPressed: () {
              setState(() {
                _liveTranscript = _sampleUtterances[_selectedLanguage]![0];
              });
              _speakFeedback(_liveTranscript);
            },
          ),
          const SizedBox(width: 8),
          ActionChip(
            avatar: const Icon(Icons.play_circle_fill, size: 16, color: AppColors.forestGreen),
            label: Text(_selectedLanguage == 'hi' ? 'नमूना 2: किराना स्टोर' : 'Sample: Electronics'),
            onPressed: () {
              setState(() {
                _liveTranscript = _sampleUtterances[_selectedLanguage]![1];
              });
              _speakFeedback(_liveTranscript);
            },
          ),
        ],
      ),
    );
  }

  Widget _buildStatusBadge() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: _isRecording ? AppColors.error.withValues(alpha: 0.1) : AppColors.brandBlue.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: _isRecording ? AppColors.error : AppColors.brandBlue,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 8),
          Text(
            _isRecording 
                ? (_selectedLanguage == 'hi' ? 'रिकॉर्डिंग चालू है... (Whisper ASR)' : 'Recording... (Whisper ASR Live)')
                : (_selectedLanguage == 'hi' ? 'माइक तैयार है' : 'Ready to capture'),
            style: TextStyle(
              color: _isRecording ? AppColors.error : AppColors.brandBlue,
              fontWeight: FontWeight.w600,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMicButton() {
    return GestureDetector(
      onTap: _toggleRecording,
      child: AnimatedBuilder(
        animation: _pulseAnimation,
        builder: (context, child) {
          return Container(
            width: 80 * (_isRecording ? _pulseAnimation.value : 1.0),
            height: 80 * (_isRecording ? _pulseAnimation.value : 1.0),
            decoration: BoxDecoration(
              color: _isRecording ? AppColors.error : AppColors.forestGreen,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: (_isRecording ? AppColors.error : AppColors.forestGreen).withValues(alpha: 0.3),
                  blurRadius: _isRecording ? 20 : 10,
                  spreadRadius: _isRecording ? 4 : 0,
                ),
              ],
            ),
            child: Icon(
              _isRecording ? Icons.mic : Icons.mic_none,
              color: AppColors.white,
              size: 38,
            ),
          );
        },
      ),
    );
  }

  Widget _buildStopButton() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: SizedBox(
        width: double.infinity,
        child: ElevatedButton.icon(
          onPressed: () {
            if (_isRecording) {
              _toggleRecording();
            }
            widget.onNavigateToReview();
          },
          icon: const Icon(Icons.arrow_forward_rounded, size: 20),
          label: Text(_selectedLanguage == 'hi' ? 'पुष्टि करें और आगे बढ़ें' : 'Extract Schema & Review'),
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.brandBlue,
            foregroundColor: AppColors.white,
            padding: const EdgeInsets.symmetric(vertical: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
      ),
    );
  }
}
