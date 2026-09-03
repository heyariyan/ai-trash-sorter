import 'package:flutter/material.dart';
import '../models/sorting_event.dart';
import '../theme/app_theme.dart';

class BinGaugesGrid extends StatelessWidget {
  final Map<String, BinStatus> bins;

  const BinGaugesGrid({super.key, required this.bins});

  @override
  Widget build(BuildContext context) {
    const categories = ['BIODEGRADABLE', 'PLASTIC', 'METAL', 'OTHER'];

    return LayoutBuilder(
      builder: (context, constraints) {
        final crossAxisCount = constraints.maxWidth > 650 ? 4 : 2;
        return GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: crossAxisCount,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: constraints.maxWidth > 650 ? 1.35 : 1.25,
          ),
          itemCount: categories.length,
          itemBuilder: (context, index) {
            final cat = categories[index];
            final binStatus = bins[cat] ?? BinStatus(category: cat);
            return _BinGaugeCard(bin: binStatus);
          },
        );
      },
    );
  }
}

class _BinGaugeCard extends StatelessWidget {
  final BinStatus bin;

  const _BinGaugeCard({required this.bin});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final catColor = AppTheme.getCategoryColor(bin.category);
    final catIcon = AppTheme.getCategoryIcon(bin.category);
    final fillPct = bin.fillPercentage;
    final pctInt = (fillPct * 100).toInt();
    final isNearFull = bin.isNearFull;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isDark ? AppTheme.darkSurface : Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isNearFull
              ? AppTheme.errorColor
              : (isDark ? AppTheme.darkBorder.withValues(alpha: 0.4) : const Color(0xFFE2E8F0)),
          width: isNearFull ? 1.5 : 1.0,
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
                  color: catColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(catIcon, color: catColor, size: 18),
              ),
              if (isNearFull)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppTheme.errorColor.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Text(
                    'FULL',
                    style: TextStyle(
                      color: AppTheme.errorColor,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                )
              else
                Text(
                  '$pctInt%',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                    color: catColor,
                  ),
                ),
            ],
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                bin.category,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                  letterSpacing: 0.3,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 2),
              Text(
                bin.distanceCm != null
                    ? '${bin.distanceCm!.toStringAsFixed(1)} cm free'
                    : 'No sensor data',
                style: TextStyle(
                  fontSize: 11,
                  color: isDark ? Colors.white60 : Colors.black54,
                ),
              ),
            ],
          ),
          // Fill Progress Bar
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: fillPct,
              minHeight: 6,
              backgroundColor: isDark ? AppTheme.darkCard : const Color(0xFFE2E8F0),
              valueColor: AlwaysStoppedAnimation<Color>(
                isNearFull ? AppTheme.errorColor : catColor,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
