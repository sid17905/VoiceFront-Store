import 'package:flutter/material.dart';
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
  final whatsappController = TextEditingController();
  final price1Controller = TextEditingController();
  final price2Controller = TextEditingController();
  String category = 'Food & Beverages';

  @override
  void dispose() {
    shopNameController.dispose();
    locationController.dispose();
    whatsappController.dispose();
    price1Controller.dispose();
    price2Controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('VoiceFront'),
        actions: const [
          Padding(
            padding: EdgeInsets.all(14),
            child: Icon(Icons.help_outline, size: 24),
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
          'Review & Edit',
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.w700,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'Check your details before we build your storefront.',
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
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
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
                'Your Voice Input',
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: AppColors.brandBlue,
                  fontSize: 14,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Text(
            '"I want to open a shop called Krishna Sweets for selling milk products and samosas in Jaipur. I need to be open from 8 AM to 9 PM and people can contact me on WhatsApp."',
            style: TextStyle(
              fontStyle: FontStyle.italic,
              color: AppColors.textPrimary,
              fontSize: 13,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFormSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Expanded(
              child: Text(
                'Storefront Details',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
            ),
            TextButton.icon(
              onPressed: () {},
              icon: const Icon(Icons.add, size: 18, color: AppColors.brandBlue),
              label: const Text(
                '+ Add More',
                style: TextStyle(
                  color: AppColors.brandBlue,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
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
        _buildProductRow('Samosas', price2Controller, true),
        const SizedBox(height: 4),
        const Padding(
          padding: EdgeInsets.only(left: 4),
          child: Text(
            'Price required for Samosas',
            style: TextStyle(color: AppColors.error, fontSize: 12),
          ),
        ),
        const SizedBox(height: 20),
        _buildField(
          'WhatsApp Number',
          whatsappController,
          prefix: '+91 ',
          suffixIcon: const Icon(Icons.error_outline, color: AppColors.error, size: 20),
        ),
        const SizedBox(height: 16),
        _buildFieldWithIcon(
          'City/Location',
          locationController,
          Icons.location_on_outlined,
        ),
        const SizedBox(height: 16),
        _buildTimePickers(),
      ],
    );
  }

  Widget _buildField(String label, TextEditingController controller,
      {String? prefix, Widget? suffixIcon}) {
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
            suffixIcon: suffixIcon,
            filled: true,
            fillColor: AppColors.white,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: Color(0xFFE5E7EB)),
            ),
            enabledBorder: OutlineInputBorder(
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
                DropdownMenuItem(value: 'Food & Beverages', child: Text('Food & Beverages')),
                DropdownMenuItem(value: 'Apparel', child: Text('Apparel')),
                DropdownMenuItem(value: 'Electronics', child: Text('Electronics')),
                DropdownMenuItem(value: 'Pharmacy', child: Text('Pharmacy')),
                DropdownMenuItem(value: 'Services', child: Text('Services')),
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
                color: hasError ? AppColors.error : const Color(0xFFE5E7EB),
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
                    style: const TextStyle(fontSize: 14),
                  ),
                ),
                if (hasError)
                  const Icon(Icons.error_outline, color: AppColors.error, size: 16),
              ],
            ),
          ),
        ),
        const SizedBox(width: 8),
        IconButton(
          onPressed: () {},
          icon: const Icon(Icons.delete_outline, color: AppColors.error, size: 22),
          padding: EdgeInsets.zero,
          constraints: const BoxConstraints(),
        ),
      ],
    );
  }

  Widget _buildFieldWithIcon(
      String label, TextEditingController controller, IconData icon) {
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
            prefixIcon: Icon(icon, color: AppColors.brandBlue, size: 20),
            filled: true,
            fillColor: AppColors.white,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: Color(0xFFE5E7EB)),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: Color(0xFFE5E7EB)),
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          ),
        ),
      ],
    );
  }

  Widget _buildTimePickers() {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Business Hours',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 6),
              _buildTimeDropdown('08:00 AM'),
            ],
          ),
        ),
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 12, vertical: 24),
          child: Text(
            'to',
            style: TextStyle(color: AppColors.textSecondary, fontSize: 14),
          ),
        ),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 25),
              _buildTimeDropdown('09:00 PM'),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildTimeDropdown(String value) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          isExpanded: true,
          items: const [
            DropdownMenuItem(value: '08:00 AM', child: Text('08:00 AM')),
            DropdownMenuItem(value: '09:00 AM', child: Text('09:00 AM')),
            DropdownMenuItem(value: '10:00 AM', child: Text('10:00 AM')),
            DropdownMenuItem(value: '05:00 PM', child: Text('05:00 PM')),
            DropdownMenuItem(value: '09:00 PM', child: Text('09:00 PM')),
          ],
          onChanged: (_) {},
        ),
      ),
    );
  }

  Widget _buildConfirmButton() {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 16),
      child: FloatingActionButton.extended(
        onPressed: widget.onNavigateToPreview,
        backgroundColor: AppColors.forestGreen,
        foregroundColor: AppColors.white,
        elevation: 4,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        label: const Text(
          'Confirm & Generate / पुष्टि करें और बनाएं',
          style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
        ),
        icon: const Icon(Icons.check_circle_outline, size: 22),
      ),
    );
  }
}
