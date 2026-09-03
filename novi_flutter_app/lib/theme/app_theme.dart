import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // Brand Colors
  static const Color primaryGreen = Color(0xFF10B981); // Emerald 500
  static const Color primaryGreenDark = Color(0xFF059669);
  static const Color accentCyan = Color(0xFF06B6D4); // Cyan 500
  static const Color darkBg = Color(0xFF0F172A); // Slate 900
  static const Color darkSurface = Color(0xFF1E293B); // Slate 800
  static const Color darkCard = Color(0xFF334155); // Slate 700
  static const Color darkBorder = Color(0xFF475569);

  // Category Colors
  static const Color biodegradableColor = Color(0xFF10B981); // Emerald
  static const Color plasticColor = Color(0xFF0284C7); // Sky Blue
  static const Color metalColor = Color(0xFFF59E0B); // Amber
  static const Color otherColor = Color(0xFF8B5CF6); // Purple / Violet
  static const Color errorColor = Color(0xFFEF4444); // Red 500
  static const Color warningColor = Color(0xFFF97316); // Orange 500

  static Color getCategoryColor(String? category) {
    if (category == null) return Colors.grey;
    switch (category.toUpperCase()) {
      case 'BIODEGRADABLE':
        return biodegradableColor;
      case 'PLASTIC':
        return plasticColor;
      case 'METAL':
        return metalColor;
      case 'OTHER':
        return otherColor;
      default:
        return Colors.blueGrey;
    }
  }

  static IconData getCategoryIcon(String? category) {
    if (category == null) return Icons.help_outline;
    switch (category.toUpperCase()) {
      case 'BIODEGRADABLE':
        return Icons.eco;
      case 'PLASTIC':
        return Icons.water_drop;
      case 'METAL':
        return Icons.hardware;
      case 'OTHER':
        return Icons.inventory_2;
      default:
        return Icons.delete_outline;
    }
  }

  static ThemeData get darkTheme {
    final baseText = GoogleFonts.outfitTextTheme(ThemeData.dark().textTheme);
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: darkBg,
      colorScheme: ColorScheme.dark(
        primary: primaryGreen,
        secondary: accentCyan,
        surface: darkSurface,
        surfaceContainerHighest: darkCard,
        error: errorColor,
        onPrimary: Colors.black,
        onSecondary: Colors.black,
        onSurface: Colors.white,
      ),
      textTheme: baseText.copyWith(
        headlineLarge: baseText.headlineLarge?.copyWith(
          fontWeight: FontWeight.bold,
          letterSpacing: -0.5,
          color: Colors.white,
        ),
        headlineMedium: baseText.headlineMedium?.copyWith(
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
        titleLarge: baseText.titleLarge?.copyWith(
          fontWeight: FontWeight.w600,
          color: Colors.white,
        ),
        titleMedium: baseText.titleMedium?.copyWith(
          fontWeight: FontWeight.w600,
          color: Colors.white70,
        ),
        bodyLarge: baseText.bodyLarge?.copyWith(color: Colors.white),
        bodyMedium: baseText.bodyMedium?.copyWith(color: Colors.white70),
        bodySmall: baseText.bodySmall?.copyWith(color: Colors.white60),
      ),
      cardTheme: CardThemeData(
        color: darkSurface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: Color(0xFF334155), width: 1),
        ),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: darkSurface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: Color(0xFF334155)),
        ),
      ),
      navigationRailTheme: NavigationRailThemeData(
        backgroundColor: const Color(0xFF090D16),
        selectedIconTheme: const IconThemeData(color: primaryGreen, size: 26),
        unselectedIconTheme: const IconThemeData(color: Colors.white54, size: 24),
        selectedLabelTextStyle: GoogleFonts.outfit(
          color: primaryGreen,
          fontWeight: FontWeight.bold,
          fontSize: 13,
        ),
        unselectedLabelTextStyle: GoogleFonts.outfit(
          color: Colors.white54,
          fontSize: 12,
        ),
        indicatorColor: primaryGreen.withValues(alpha: 0.15),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: const Color(0xFF090D16),
        indicatorColor: primaryGreen.withValues(alpha: 0.2),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return GoogleFonts.outfit(
              color: primaryGreen,
              fontWeight: FontWeight.w600,
              fontSize: 12,
            );
          }
          return GoogleFonts.outfit(
            color: Colors.white60,
            fontSize: 12,
          );
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return const IconThemeData(color: primaryGreen);
          }
          return const IconThemeData(color: Colors.white60);
        }),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: primaryGreen,
          foregroundColor: Colors.black,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          textStyle: GoogleFonts.outfit(fontWeight: FontWeight.w600, fontSize: 14),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: darkCard.withValues(alpha: 0.5),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: darkBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: darkBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: primaryGreen, width: 2),
        ),
        labelStyle: const TextStyle(color: Colors.white70),
        hintStyle: const TextStyle(color: Colors.white38),
      ),
    );
  }

  static ThemeData get lightTheme {
    final baseText = GoogleFonts.outfitTextTheme(ThemeData.light().textTheme);
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: const Color(0xFFF8FAFC),
      colorScheme: ColorScheme.light(
        primary: primaryGreenDark,
        secondary: accentCyan,
        surface: Colors.white,
        surfaceContainerHighest: const Color(0xFFF1F5F9),
        error: errorColor,
        onPrimary: Colors.white,
        onSecondary: Colors.white,
        onSurface: const Color(0xFF0F172A),
      ),
      textTheme: baseText.copyWith(
        headlineLarge: baseText.headlineLarge?.copyWith(
          fontWeight: FontWeight.bold,
          letterSpacing: -0.5,
          color: const Color(0xFF0F172A),
        ),
        headlineMedium: baseText.headlineMedium?.copyWith(
          fontWeight: FontWeight.bold,
          color: const Color(0xFF0F172A),
        ),
        titleLarge: baseText.titleLarge?.copyWith(
          fontWeight: FontWeight.w600,
          color: const Color(0xFF0F172A),
        ),
        titleMedium: baseText.titleMedium?.copyWith(
          fontWeight: FontWeight.w600,
          color: const Color(0xFF334155),
        ),
        bodyLarge: baseText.bodyLarge?.copyWith(color: const Color(0xFF0F172A)),
        bodyMedium: baseText.bodyMedium?.copyWith(color: const Color(0xFF475569)),
        bodySmall: baseText.bodySmall?.copyWith(color: const Color(0xFF64748B)),
      ),
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: 1,
        shadowColor: Colors.black.withValues(alpha: 0.05),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: Color(0xFFE2E8F0), width: 1),
        ),
      ),
      navigationRailTheme: NavigationRailThemeData(
        backgroundColor: Colors.white,
        selectedIconTheme: const IconThemeData(color: primaryGreenDark, size: 26),
        unselectedIconTheme: const IconThemeData(color: Color(0xFF64748B), size: 24),
        selectedLabelTextStyle: GoogleFonts.outfit(
          color: primaryGreenDark,
          fontWeight: FontWeight.bold,
          fontSize: 13,
        ),
        unselectedLabelTextStyle: GoogleFonts.outfit(
          color: const Color(0xFF64748B),
          fontSize: 12,
        ),
        indicatorColor: primaryGreen.withValues(alpha: 0.15),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: Colors.white,
        indicatorColor: primaryGreen.withValues(alpha: 0.15),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return GoogleFonts.outfit(
              color: primaryGreenDark,
              fontWeight: FontWeight.w600,
              fontSize: 12,
            );
          }
          return GoogleFonts.outfit(
            color: const Color(0xFF64748B),
            fontSize: 12,
          );
        }),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: primaryGreenDark,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
          textStyle: GoogleFonts.outfit(fontWeight: FontWeight.w600, fontSize: 14),
        ),
      ),
    );
  }
}
