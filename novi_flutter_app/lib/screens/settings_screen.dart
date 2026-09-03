import 'package:flutter/material.dart';
import '../services/firebase_service.dart';
import '../theme/app_theme.dart';

class SettingsScreen extends StatefulWidget {
  final FirebaseService firebase;
  final String deviceId;
  final VoidCallback? onToggleTheme;
  final bool isDarkMode;

  const SettingsScreen({
    super.key,
    required this.firebase,
    required this.deviceId,
    this.onToggleTheme,
    this.isDarkMode = true,
  });

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  @override
  Widget build(BuildContext context) {
    final user = widget.firebase.currentUser;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: isDark ? AppTheme.darkBg : const Color(0xFFF8FAFC),
        elevation: 0,
        title: const Text('Settings & Configuration', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Account / Operator Section
          Text('Operator Session', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: isDark ? AppTheme.darkSurface : Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isDark ? AppTheme.darkBorder.withValues(alpha: 0.5) : const Color(0xFFE2E8F0),
              ),
            ),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 24,
                  backgroundColor: AppTheme.primaryGreen.withValues(alpha: 0.2),
                  child: const Icon(Icons.person, color: AppTheme.primaryGreen, size: 24),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        user?.email ?? 'Ariyan Haque (Operator)',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        user != null ? 'Authenticated via Firebase Auth' : 'Live Monitor / Guest Session',
                        style: TextStyle(
                          fontSize: 12,
                          color: isDark ? Colors.white60 : Colors.black54,
                        ),
                      ),
                    ],
                  ),
                ),
                if (user != null)
                  FilledButton.tonal(
                    onPressed: () async {
                      await widget.firebase.signOut();
                    },
                    child: const Text('Sign Out'),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // App Preferences
          Text('Preferences & Modes', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Container(
            decoration: BoxDecoration(
              color: isDark ? AppTheme.darkSurface : Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isDark ? AppTheme.darkBorder.withValues(alpha: 0.5) : const Color(0xFFE2E8F0),
              ),
            ),
            child: Column(
              children: [
                SwitchListTile(
                  secondary: const Icon(Icons.palette_outlined),
                  title: const Text('Dark Mode Theme'),
                  subtitle: const Text('Cyber-Eco aesthetic palette'),
                  value: widget.isDarkMode,
                  onChanged: (val) {
                    if (widget.onToggleTheme != null) {
                      widget.onToggleTheme!();
                    }
                  },
                ),
                const Divider(height: 1),
                SwitchListTile(
                  secondary: Icon(
                    Icons.sensors_outlined,
                    color: widget.firebase.demoMode ? AppTheme.warningColor : null,
                  ),
                  title: const Text('Demo / Simulation Mode'),
                  subtitle: const Text('Simulates live sensors & carousel when Pi is offline'),
                  value: widget.firebase.demoMode,
                  onChanged: (val) {
                    setState(() {
                      if (val) {
                        widget.firebase.startDemoSimulation();
                      } else {
                        widget.firebase.stopDemoSimulation();
                      }
                    });
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Cloud & Hardware Connection
          Text('Hardware & Firebase Config', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Container(
            decoration: BoxDecoration(
              color: isDark ? AppTheme.darkSurface : Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isDark ? AppTheme.darkBorder.withValues(alpha: 0.5) : const Color(0xFFE2E8F0),
              ),
            ),
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.developer_board),
                  title: const Text('Configured Device ID'),
                  subtitle: Text(widget.deviceId, style: const TextStyle(fontFamily: 'monospace')),
                ),
                const Divider(height: 1),
                const ListTile(
                  leading: Icon(Icons.cloud_sync_outlined),
                  title: Text('Firebase Database Host'),
                  subtitle: Text('trash2444-default-rtdb.asia-southeast1.firebasedatabase.app', style: TextStyle(fontSize: 11)),
                ),
                const Divider(height: 1),
                const ListTile(
                  leading: Icon(Icons.folder_shared_outlined),
                  title: Text('Firebase Storage Bucket'),
                  subtitle: Text('trash2444.firebasestorage.app', style: TextStyle(fontSize: 11)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // About Novi Project
          Text('About Novi AI', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: isDark ? AppTheme.darkSurface : Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isDark ? AppTheme.darkBorder.withValues(alpha: 0.5) : const Color(0xFFE2E8F0),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryGreen.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.delete_sweep, color: AppTheme.primaryGreen, size: 24),
                    ),
                    const SizedBox(width: 12),
                    const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Novi AI Smart Dustbin', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        Text('App Version 2.0.0 (Web & Mobile)', style: TextStyle(fontSize: 12, color: Colors.grey)),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  'Novi is an intelligent, autonomous waste-sorting robotic dustbin designed to automatically classify and separate discarded waste into 4 distinct compartments (Biodegradable, Plastic, Metal, Other). Powered by a Raspberry Pi 3B+, NEMA 17 stepper carousel, MG995 servo gate, dual ultrasonic sensors, and on-device MobileNetV2 AI vision.',
                  style: TextStyle(
                    fontSize: 12,
                    height: 1.5,
                    color: isDark ? Colors.white70 : Colors.black87,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 40),
        ],
      ),
    );
  }
}
