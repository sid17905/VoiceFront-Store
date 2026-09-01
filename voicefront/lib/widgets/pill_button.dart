import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class PillButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final Color backgroundColor;
  final Color textColor;
  final IconData? icon;
  final bool isExpanded;
  final bool isDisabled;

  const PillButton({
    super.key,
    required this.text,
    this.onPressed,
    this.backgroundColor = AppColors.brandBlue,
    this.textColor = AppColors.white,
    this.icon,
    this.isExpanded = false,
    this.isDisabled = false,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveColor = isDisabled ? AppColors.grey : backgroundColor;
    return SizedBox(
      width: isExpanded ? double.infinity : null,
      child: ElevatedButton.icon(
        onPressed: isDisabled ? null : onPressed,
        icon: Icon(icon, size: 18, color: textColor),
        label: Text(
          text,
          style: TextStyle(
            color: isDisabled ? AppColors.white : textColor,
            fontWeight: FontWeight.w600,
            fontSize: 15,
          ),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: effectiveColor,
          foregroundColor: textColor,
          disabledBackgroundColor: effectiveColor,
          disabledForegroundColor: AppColors.white,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(25),
          ),
          elevation: 0,
        ),
      ),
    );
  }
}
