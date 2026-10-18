import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_colors.dart';

class AppTheme {
  /// google_fonts >= 9 depends on package:material_ui, whose TextTheme type is
  /// not assignable to Flutter's. `GoogleFonts.inter()` returns a TextStyle
  /// whose `fontFamily` is what the theme actually needs, so set that instead
  /// of passing a Flutter TextTheme through interTextTheme().
  static String? get _fontFamily => GoogleFonts.inter().fontFamily;

  static ThemeData lightTheme() {
    final scheme = ColorScheme.fromSeed(seedColor: AppColors.brandBlue, brightness: Brightness.light);
    return ThemeData(
      colorScheme: scheme,
      useMaterial3: true,
      brightness: Brightness.light,
      fontFamily: _fontFamily,
      primaryColor: scheme.primary,
      scaffoldBackgroundColor: scheme.surface,
      appBarTheme: AppBarTheme(
        backgroundColor: scheme.surface,
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
      fontFamily: _fontFamily,
      primaryColor: scheme.primary,
      scaffoldBackgroundColor: scheme.surface,
      appBarTheme: AppBarTheme(
        backgroundColor: scheme.surface,
        iconTheme: IconThemeData(color: scheme.onSurface),
      ),
    );
  }
}
