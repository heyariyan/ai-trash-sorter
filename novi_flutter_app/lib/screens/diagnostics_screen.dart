import 'package:flutter/material.dart';
import '../models/sorting_event.dart';
import '../services/firebase_service.dart';
import '../theme/app_theme.dart';

class DiagnosticsScreen extends StatefulWidget {
  final FirebaseService firebase;
  final String deviceId;

  const DiagnosticsScreen({
    super.key,
    required this.firebase,
    required this.deviceId,
  });

  @override
  State<DiagnosticsScreen> createState() => _DiagnosticsScreenState();
}

class _DiagnosticsScreenState extends State<DiagnosticsScreen> {
  bool _homing = false;

  Future<void> _triggerHome() async {
    setState(() => _homing = true);
    try {
      await widget.firebase.requestHome();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Homing calibration requested on Raspberry Pi'),
            backgroundColor: AppTheme.primaryGreenDark,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error triggering calibration: $e'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _homing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return StreamBuilder<DeviceStatus>(
      stream: widget.firebase.statusStream(),
      builder: (context, statusSnap) {
        final status = statusSnap.data ?? DeviceStatus.empty;
        final isOnline = status.isOnline;

        return Scaffold(
          appBar: AppBar(
            backgroundColor: isDark ? AppTheme.darkBg : const Color(0xFFF8FAFC),
            elevation: 0,
            title: const Text('Hardware & Diagnostics', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
          body: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Controller Hub Status
              _buildControllerCard(status, isDark),
              const SizedBox(height: 16),

              // Sensor Telemetry Cards Grid
              Text('Sensors & Actuators', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              _buildSensorsGrid(status, isDark),
              const SizedBox(height: 24),

              // Embedded Hardware Specs
              Text('Hardware Calibration Specs', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              _buildSpecsCard(isDark),
              const SizedBox(height: 24),

              // Diagnostics Actions
              Text('Diagnostic Actions', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              _buildActionsCard(isOnline, isDark),
              const SizedBox(height: 40),
            ],
          ),
        );
      },
    );
  }

  Widget _buildControllerCard(DeviceStatus status, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: isDark ? AppTheme.darkSurface : Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isDark ? AppTheme.darkBorder.withValues(alpha: 0.5) : const Color(0xFFE2E8F0),
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppTheme.primaryGreen.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.memory, color: AppTheme.primaryGreen, size: 28),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Raspberry Pi 3B+ (Master Sorter)',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                ),
                const SizedBox(height: 2),
                Text(
                  'Device ID: ${widget.deviceId} • Model: ${status.modelVersion ?? "v1.4-mobilenetv2"}',
                  style: TextStyle(
                    fontSize: 12,
                    color: isDark ? Colors.white60 : Colors.black54,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Active State: ${status.state.isEmpty ? "OFFLINE" : status.state}',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: status.isOnline ? AppTheme.primaryGreen : Colors.grey,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSensorsGrid(DeviceStatus status, bool isDark) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isWide = constraints.maxWidth > 600;
        return GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: isWide ? 3 : 2,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: isWide ? 1.35 : 1.25,
          children: [
            _sensorCard(
              title: 'U1 Intake Sensor',
              value: status.intakeDistanceCm != null
                  ? '${status.intakeDistanceCm!.toStringAsFixed(1)} cm'
                  : (status.state == 'DETECTED' ? 'Object Detected' : 'Standby'),
              subtitle: 'Ultrasonic Trigger',
              icon: Icons.sensors,
              color: AppTheme.accentCyan,
              isDark: isDark,
            ),
            _sensorCard(
              title: 'U3 Bin Sensor',
              value: status.binDistanceCm != null
                  ? '${status.binDistanceCm!.toStringAsFixed(1)} cm'
                  : 'Active',
              subtitle: 'Clearance Depth',
              icon: Icons.radar,
              color: AppTheme.primaryGreen,
              isDark: isDark,
            ),
            _sensorCard(
              title: 'IR Home Sensor',
              value: status.positionKnown ? 'Calibrated' : 'Needs Homing',
              subtitle: 'Hall-Effect Switch',
              icon: Icons.adjust,
              color: status.positionKnown ? AppTheme.primaryGreen : AppTheme.warningColor,
              isDark: isDark,
            ),
            _sensorCard(
              title: 'NEMA 17 Stepper',
              value: status.currentPosition ?? 'HOME',
              subtitle: 'DRV8825 Driver',
              icon: Icons.rotate_90_degrees_cw,
              color: AppTheme.metalColor,
              isDark: isDark,
            ),
            _sensorCard(
              title: 'MG995 Servo Gate',
              value: status.state == 'DROPPING' ? 'OPEN (90°)' : 'CLOSED (0°)',
              subtitle: 'Drop Hatch',
              icon: Icons.door_sliding,
              color: AppTheme.otherColor,
              isDark: isDark,
            ),
            _sensorCard(
              title: 'SSD1306 OLED',
              value: 'I2C 0x3C OK',
              subtitle: '128x64 Display',
              icon: Icons.tv,
              color: Colors.teal,
              isDark: isDark,
            ),
          ],
        );
      },
    );
  }

  Widget _sensorCard({
    required String title,
    required String value,
    required String subtitle,
    required IconData icon,
    required Color color,
    required bool isDark,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isDark ? AppTheme.darkSurface : Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isDark ? AppTheme.darkBorder.withValues(alpha: 0.4) : const Color(0xFFE2E8F0),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: color, size: 18),
              ),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                value,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 2),
              Text(
                title,
                style: TextStyle(
                  fontSize: 11,
                  color: isDark ? Colors.white70 : Colors.black87,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              Text(
                subtitle,
                style: TextStyle(
                  fontSize: 10,
                  color: isDark ? Colors.white38 : Colors.black38,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSpecsCard(bool isDark) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isDark ? AppTheme.darkSurface : Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isDark ? AppTheme.darkBorder.withValues(alpha: 0.5) : const Color(0xFFE2E8F0),
        ),
      ),
      child: Column(
        children: [
          _specRow('Stepper Motor', 'NEMA 17 (17HS3401) • 200 steps/rev (50 steps/90°)', isDark),
          const Divider(height: 16),
          _specRow('Pulse Delay', '0.005s with Trapezoidal Acceleration Ramp', isDark),
          const Divider(height: 16),
          _specRow('Trigger Threshold', 'Ultrasonic confidence 0.60, threshold 7.0 cm', isDark),
          const Divider(height: 16),
          _specRow('Servo Angles', 'Closed: 0.0°, Open: 90.0° • Settle 0.7s', isDark),
          const Divider(height: 16),
          _specRow('AI Model', 'TensorFlow Lite INT8 quantized MobileNetV2', isDark),
        ],
      ),
    );
  }

  Widget _specRow(String label, String value, bool isDark) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 120,
          child: Text(
            label,
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: isDark ? Colors.white70 : Colors.black87),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(fontSize: 12, color: isDark ? Colors.white60 : Colors.black54),
          ),
        ),
      ],
    );
  }

  Widget _buildActionsCard(bool isOnline, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(16),
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
            contentPadding: EdgeInsets.zero,
            leading: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppTheme.primaryGreen.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.home_outlined, color: AppTheme.primaryGreen),
            ),
            title: const Text('Request Carousel Homing', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            subtitle: const Text('Rotates carousel until IR home sensor trips', style: TextStyle(fontSize: 12)),
            trailing: FilledButton.tonal(
              onPressed: _homing ? null : _triggerHome,
              child: Text(_homing ? 'Homing...' : 'Execute'),
            ),
          ),
        ],
      ),
    );
  }
}
