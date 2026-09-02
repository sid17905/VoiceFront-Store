import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import '../theme/app_colors.dart';

class ReviewEditScreen extends StatefulWidget {
  final VoidCallback onNavigateToPreview;

  const ReviewEditScreen({super.key, required this.onNavigateToPreview});

  @override
  State<ReviewEditScreen> createState() => _ReviewEditScreenState();
}

class _ReviewEditScreenState extends State<ReviewEditScreen> {
  final shopNameController = TextEditingController(text: 'Krishna Sweets');
  final locationController = TextEditingController(text: 'Jaipur');
  final whatsappController = TextEditingController(text: '9876543210');
  final price1Controller = TextEditingController(text: '180');
  final price2Controller = TextEditingController(text: '20');
  String category = 'Food & Beverages';
  final FlutterTts _flutterTts = FlutterTts();

  @override
  void dispose() {
    shopNameController.dispose();
    locationController.dispose();
    whatsappController.dispose();
    price1Controller.dispose();
    price2Controller.dispose();
    _flutterTts.stop();
    super.dispose();
  }

  void _speakSummary() async {
    String textToSpeak = "Shop Name: ${shopNameController.text}. Category: $category. Location: ${locationController.text}. Detected items: Milk Products and Samosas.";
    await _flutterTts.speak(textToSpeak);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Review Schema Draft'),
        actions: [
          IconButton(
            icon: const Icon(Icons.volume_up, color: AppColors.brandBlue),
            tooltip: 'Read schema aloud',
            onPressed: _speakSummary,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(),
            const SizedBox(height: 20),
            _buildVoiceInputCard(),
            const SizedBox(height: 24),
            _buildFormSection(),
            const SizedBox(height: 100),
          ],
        ),
      ),
      floatingActionButton: _buildConfirmButton(),
    );
  }

  Widget _buildHeader() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Schema Builder Output',
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.w700,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'IndicBERT tagged entities mapped to StorefrontSpec JSON.',
          style: TextStyle(
            fontSize: 14,
            color: AppColors.textSecondary.withValues(alpha: 0.8),
          ),
        ),
      ],
    );
  }

  Widget _buildVoiceInputCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.lightBlue,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.brandBlue.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: AppColors.brandBlue.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(
                      Icons.graphic_eq,
                      color: AppColors.brandBlue,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 10),
                  const Text(
                    'NER Extracted Spans',
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: AppColors.brandBlue,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
              const Chip(
                label: Text('94.7% Conf.', style: TextStyle(fontSize: 10, color: AppColors.forestGreen, fontWeight: FontWeight.bold)),
                backgroundColor: AppColors.white,
                padding: EdgeInsets.zero,
              )
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              _buildEntityChip('SHOP_NAME', 'Krishna Sweets', AppColors.brandBlue),
              _buildEntityChip('CATEGORY', 'Food / Sweets', AppColors.forestGreen),
              _buildEntityChip('PRODUCT', 'Milk Products (₹180)', AppColors.brown),
              _buildEntityChip('PRODUCT', 'Samosas (₹20)', AppColors.brown),
              _buildEntityChip('LOCATION', 'Jaipur', AppColors.darkGreenTag),
              _buildEntityChip('HOURS', '08:00 - 21:00', AppColors.textSecondary),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildEntityChip(String tag, String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: RichText(
        text: TextSpan(
          children: [
            TextSpan(
              text: '$tag: ',
              style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: color),
            ),
            TextSpan(
              text: text,
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFormSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Storefront Details (Validated)',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w700,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 16),
        _buildField('Shop Name', shopNameController),
        const SizedBox(height: 16),
        _buildDropdown(),
        const SizedBox(height: 20),
        const Text(
          'Products Detected',
          style: TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 12),
        _buildProductRow('Milk Products', price1Controller, false),
        const SizedBox(height: 10),
        _buildProductRow('Samosas', price2Controller, false),
        const SizedBox(height: 20),
        _buildField(
          'WhatsApp Number',
          whatsappController,
          prefix: '+91 ',
        ),
        const SizedBox(height: 16),
        _buildField(
          'City/Location',
          locationController,
        ),
      ],
    );
  }

  Widget _buildField(String label, TextEditingController controller, {String? prefix}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w500,
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 6),
        TextField(
          controller: controller,
          decoration: InputDecoration(
            prefixText: prefix,
            filled: true,
            fillColor: AppColors.white,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: Color(0xFFE5E7EB)),
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          ),
        ),
      ],
    );
  }

  Widget _buildDropdown() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Category',
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w500,
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 6),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 14),
          decoration: BoxDecoration(
            color: AppColors.white,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: const Color(0xFFE5E7EB)),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: category,
              isExpanded: true,
              items: const [
                DropdownMenuItem(value: 'Food & Beverages', child: Text('Food & Beverages (food.jinja2)')),
                DropdownMenuItem(value: 'Apparel', child: Text('Apparel (apparel.jinja2)')),
                DropdownMenuItem(value: 'Electronics', child: Text('Electronics (electronics.jinja2)')),
                DropdownMenuItem(value: 'Pharmacy', child: Text('Pharmacy (pharmacy.jinja2)')),
                DropdownMenuItem(value: 'Services', child: Text('Services (services.jinja2)')),
              ],
              onChanged: (v) => setState(() => category = v ?? category),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildProductRow(String name, TextEditingController priceCtrl, bool hasError) {
    return Row(
      children: [
        Expanded(
          flex: 3,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: AppColors.white,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFFE5E7EB)),
            ),
            child: Text(name, style: const TextStyle(fontSize: 14, color: AppColors.textPrimary)),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          flex: 2,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
            decoration: BoxDecoration(
              color: AppColors.white,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: const Color(0xFFE5E7EB),
              ),
            ),
            child: Row(
              children: [
                const Text('₹', style: TextStyle(color: AppColors.textSecondary, fontSize: 14)),
                const SizedBox(width: 4),
                Expanded(
                  child: TextField(
                    controller: priceCtrl,
                    decoration: const InputDecoration(
                      border: InputBorder.none,
                      isDense: true,
                      contentPadding: EdgeInsets.zero,
                    ),
                    keyboardType: TextInputType.number,
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildConfirmButton() {
    return Padding(
      padding: const EdgeInsets.only(left: 32),
      child: SizedBox(
        width: double.infinity,
        child: FloatingActionButton.extended(
          onPressed: widget.onNavigateToPreview,
          backgroundColor: AppColors.brandBlue,
          label: const Row(
            children: [
              Text('Generate Storefront Bundle', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              SizedBox(width: 8),
              Icon(Icons.auto_awesome, color: Colors.white, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}
