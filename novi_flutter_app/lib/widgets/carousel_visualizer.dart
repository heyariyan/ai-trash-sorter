import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class CarouselVisualizer extends StatefulWidget {
  final String? currentPosition;
  final String state;
  final bool positionKnown;

  const CarouselVisualizer({
    super.key,
    required this.currentPosition,
    required this.state,
    required this.positionKnown,
  });

  @override
  State<CarouselVisualizer> createState() => _CarouselVisualizerState();
}

class _CarouselVisualizerState extends State<CarouselVisualizer>
    with SingleTickerProviderStateMixin {
  late AnimationController _animCtrl;
  late Animation<double> _rotationAnim;
  double _currentAngle = 0.0;

  final Map<String, double> _positionAngles = {
    'BIODEGRADABLE': 0.0,
    'PLASTIC': math.pi / 2, // 90 deg
    'METAL': math.pi, // 180 deg
    'OTHER': 3 * math.pi / 2, // 270 deg
  };

  @override
  void initState() {
    super.initState();
    _animCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _currentAngle = _getTargetAngle(widget.currentPosition);
    _rotationAnim = Tween<double>(begin: _currentAngle, end: _currentAngle)
        .animate(CurvedAnimation(parent: _animCtrl, curve: Curves.easeInOutCubic));
  }

  double _getTargetAngle(String? position) {
    if (position == null) return 0.0;
    return _positionAngles[position.toUpperCase()] ?? 0.0;
  }

  @override
  void didUpdateWidget(covariant CarouselVisualizer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.currentPosition != widget.currentPosition) {
      final targetAngle = _getTargetAngle(widget.currentPosition);
      _rotationAnim = Tween<double>(begin: _currentAngle, end: targetAngle)
          .animate(CurvedAnimation(parent: _animCtrl, curve: Curves.easeInOutCubic))
        ..addListener(() {
          setState(() {
            _currentAngle = _rotationAnim.value;
          });
        });
      _animCtrl.forward(from: 0.0);
    }
  }

  @override
  void dispose() {
    _animCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isMoving = widget.state == 'MOVING';

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: isDark ? AppTheme.darkSurface : Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isDark ? AppTheme.darkBorder.withValues(alpha: 0.5) : const Color(0xFFE2E8F0),
        ),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppTheme.accentCyan.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.rotate_right, color: AppTheme.accentCyan, size: 20),
                  ),
                  const SizedBox(width: 10),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Carousel Chamber',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      Text(
                        widget.positionKnown
                            ? 'Position: ${widget.currentPosition ?? "HOME"}'
                            : 'Uncalibrated / Unknown',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: widget.positionKnown
                                  ? (isDark ? Colors.white70 : Colors.black54)
                                  : AppTheme.warningColor,
                            ),
                      ),
                    ],
                  ),
                ],
              ),
              if (isMoving)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.accentCyan.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const SizedBox(
                        width: 10,
                        height: 10,
                        child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.accentCyan),
                      ),
                      const SizedBox(width: 6),
                      Text(
                        'STEPPING',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.accentCyan,
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
          const SizedBox(height: 24),
          SizedBox(
            height: 200,
            width: 200,
            child: Stack(
              alignment: Alignment.center,
              children: [
                // Animated Custom Painter
                CustomPaint(
                  size: const Size(200, 200),
                  painter: _CarouselPainter(
                    angle: _currentAngle,
                    isDark: isDark,
                    activePosition: widget.currentPosition,
                  ),
                ),
                // Center Hub Indicator
                Container(
                  width: 54,
                  height: 54,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isDark ? AppTheme.darkBg : const Color(0xFFF1F5F9),
                    border: Border.all(
                      color: AppTheme.primaryGreen,
                      width: 2.5,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: AppTheme.primaryGreen.withValues(alpha: 0.3),
                        blurRadius: 10,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: const Center(
                    child: Icon(
                      Icons.smart_toy_outlined,
                      color: AppTheme.primaryGreen,
                      size: 24,
                    ),
                  ),
                ),
                // Fixed Top Intake Pointer
                Positioned(
                  top: 0,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppTheme.errorColor,
                      borderRadius: BorderRadius.circular(8),
                      boxShadow: [
                        BoxShadow(
                          color: AppTheme.errorColor.withValues(alpha: 0.4),
                          blurRadius: 6,
                        ),
                      ],
                    ),
                    child: const Text(
                      'DROP GATE',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          // Legend Chips
          Wrap(
            spacing: 8,
            runSpacing: 6,
            alignment: WrapAlignment.center,
            children: [
              _buildLegendChip('BIO', AppTheme.biodegradableColor, widget.currentPosition == 'BIODEGRADABLE'),
              _buildLegendChip('PLASTIC', AppTheme.plasticColor, widget.currentPosition == 'PLASTIC'),
              _buildLegendChip('METAL', AppTheme.metalColor, widget.currentPosition == 'METAL'),
              _buildLegendChip('OTHER', AppTheme.otherColor, widget.currentPosition == 'OTHER'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLegendChip(String label, Color color, bool isActive) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: isActive ? color.withValues(alpha: 0.25) : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isActive ? color : color.withValues(alpha: 0.3),
          width: isActive ? 1.5 : 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
              color: isActive ? color : (Theme.of(context).brightness == Brightness.dark ? Colors.white70 : Colors.black87),
            ),
          ),
        ],
      ),
    );
  }
}

class _CarouselPainter extends CustomPainter {
  final double angle;
  final bool isDark;
  final String? activePosition;

  _CarouselPainter({
    required this.angle,
    required this.isDark,
    required this.activePosition,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 12;

    canvas.save();
    canvas.translate(center.dx, center.dy);
    canvas.rotate(angle);

    final categories = [
      {'name': 'BIODEGRADABLE', 'color': AppTheme.biodegradableColor, 'icon': Icons.eco},
      {'name': 'PLASTIC', 'color': AppTheme.plasticColor, 'icon': Icons.water_drop},
      {'name': 'METAL', 'color': AppTheme.metalColor, 'icon': Icons.hardware},
      {'name': 'OTHER', 'color': AppTheme.otherColor, 'icon': Icons.inventory_2},
    ];

    const sweepAngle = math.pi / 2; // 90 deg per quadrant

    for (int i = 0; i < 4; i++) {
      final startAngle = (i * sweepAngle) - (math.pi / 4) - (math.pi / 2);
      final cat = categories[i];
      final color = cat['color'] as Color;
      final isSectorActive = activePosition?.toUpperCase() == cat['name'];

      final paint = Paint()
        ..style = PaintingStyle.fill
        ..color = isSectorActive
            ? color.withValues(alpha: isDark ? 0.35 : 0.25)
            : color.withValues(alpha: isDark ? 0.12 : 0.08);

      canvas.drawArc(
        Rect.fromCircle(center: Offset.zero, radius: radius),
        startAngle,
        sweepAngle - 0.04,
        true,
        paint,
      );

      final borderPaint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = isSectorActive ? 2.5 : 1.0
        ..color = isSectorActive ? color : color.withValues(alpha: 0.3);

      canvas.drawArc(
        Rect.fromCircle(center: Offset.zero, radius: radius),
        startAngle,
        sweepAngle - 0.04,
        true,
        borderPaint,
      );
    }

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant _CarouselPainter oldDelegate) {
    return oldDelegate.angle != angle ||
        oldDelegate.isDark != isDark ||
        oldDelegate.activePosition != activePosition;
  }
}
