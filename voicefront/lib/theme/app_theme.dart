
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'spacing.dart';

class AppTheme {
  static ThemeData lightTheme() {
    final scheme = ColorScheme.fromSeed(seedColor: AppColors.brandBlue, brightness: Brightness.light);
    return ThemeData(
      colorScheme: scheme,
      useMaterial3: true,
      brightness: Brightness.light,
      textTheme: GoogleFonts.interTextTheme(
        ThemeData.light().textTheme,
      ),
      primaryColor: scheme.primary,
      scaffoldBackgroundColor: scheme.background,
      appBarTheme: AppBarTheme(
        color: Colors.white,
        iconTheme: IconThemeData(color: scheme.onSurface),
      ),
    );
  }

  static ThemeData darkTheme() {
    final scheme = ColorScheme.fromSeed(seedColor: AppColors.brandBlue, brightness: Brightness.dark);
    return ThemeData(
      colorScheme: scheme,
      useMaterial3: true,
      brightness: Brightness.dark,
      textTheme: GoogleFonts.interTextTheme(
        ThemeData.dark().textTheme,
      ),
      primaryColor: scheme.primary,
      scaffoldBackgroundColor: scheme.background,
      appBarTheme: AppBarTheme(
        color: scheme.surface,
        iconTheme: IconThemeData(color: scheme.onSurface),
      ),
    );
  }
}
