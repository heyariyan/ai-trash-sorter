import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import '../models/sorting_event.dart';
import '../services/firebase_service.dart';
import '../theme/app_theme.dart';
import '../widgets/common_widgets.dart';

class StatsScreen extends StatefulWidget {
  final FirebaseService firebase;

  const StatsScreen({super.key, required this.firebase});

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> {
  int _touchedIndex = -1;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return StreamBuilder<List<SortingEvent>>(
      stream: widget.firebase.eventsStream(),
      builder: (context, snap) {
        final events = snap.data ?? [];
        if (events.isEmpty) {
          return Scaffold(
            appBar: AppBar(
              backgroundColor: isDark ? AppTheme.darkBg : const Color(0xFFF8FAFC),
              title: const Text('Analytics & AI Stats', style: TextStyle(fontWeight: FontWeight.bold)),
            ),
            body: const EmptyStateWidget(
              icon: Icons.insights_outlined,
              title: 'No analytics available',
              subtitle: 'Data will populate as objects are classified and sorted by Novi.',
            ),
          );
        }

        final stats = SorterStats.fromEvents(events);

        return Scaffold(
          appBar: AppBar(
            backgroundColor: isDark ? AppTheme.darkBg : const Color(0xFFF8FAFC),
            elevation: 0,
            title: const Text('Analytics & AI Stats', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
          body: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Top Accuracy Card
              _buildAccuracyHero(stats, isDark),
              const SizedBox(height: 16),

              // KPI Row
              LayoutBuilder(
                builder: (context, constraints) {
                  final isWide = constraints.maxWidth > 650;
                  return GridView.count(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisCount: isWide ? 4 : 2,
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: isWide ? 1.5 : 1.4,
                    children: [
                      MetricSummaryTile(
                        label: 'Total Processed',
                        value: '${stats.totalEvents}',
                        icon: Icons.inventory_2_outlined,
                        color: AppTheme.accentCyan,
                      ),
                      MetricSummaryTile(
                        label: 'Verified Correct',
                        value: '${stats.correctCount}',
                        icon: Icons.check_circle_outline,
                        color: AppTheme.primaryGreen,
                        subtitle: 'Human Verified',
                      ),
                      MetricSummaryTile(
                        label: 'Misclassified',
                        value: '${stats.incorrectCount}',
                        icon: Icons.replay_outlined,
                        color: AppTheme.warningColor,
                        subtitle: 'Corrected by User',
                      ),
                      MetricSummaryTile(
                        label: 'Pending Review',
                        value: '${stats.pendingCount}',
                        icon: Icons.pending_actions_outlined,
                        color: AppTheme.otherColor,
                        subtitle: 'Needs Review',
                      ),
                    ],
                  );
                },
              ),
              const SizedBox(height: 24),

              // Category Breakdown Chart Card
              _buildCategoryChartCard(stats, isDark),
              const SizedBox(height: 24),

              // System Latency & Hardware Performance
              _buildHardwarePerformanceCard(stats, isDark),
              const SizedBox(height: 24),

              // Bin Distribution Breakdown
              _buildBinDistributionCard(stats, isDark),
              const SizedBox(height: 40),
            ],
          ),
        );
      },
    );
  }

  Widget _buildAccuracyHero(SorterStats stats, bool isDark) {
    final judgedCount = stats.correctCount + stats.incorrectCount;

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: isDark
              ? [const Color(0xFF1E293B), const Color(0xFF0F172A)]
              : [Colors.white, const Color(0xFFF1F5F9)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isDark ? AppTheme.darkBorder.withValues(alpha: 0.5) : const Color(0xFFE2E8F0),
        ),
      ),
      child: Row(
        children: [
          // Circular Score Meter
          Stack(
            alignment: Alignment.center,
            children: [
              SizedBox(
                width: 90,
                height: 90,
                child: CircularProgressIndicator(
                  value: judgedCount > 0 ? (stats.accuracy / 100) : 1.0,
                  strokeWidth: 8,
                  backgroundColor: isDark ? AppTheme.darkCard : const Color(0xFFE2E8F0),
                  valueColor: AlwaysStoppedAnimation<Color>(
                    stats.accuracy >= 80
                        ? AppTheme.primaryGreen
                        : stats.accuracy >= 50
                            ? AppTheme.warningColor
                            : AppTheme.errorColor,
                  ),
                ),
              ),
              Text(
                '${stats.accuracy.toStringAsFixed(0)}%',
                style: const TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(width: 24),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Model Precision Rating',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Text(
                  judgedCount > 0
                      ? 'Based on $judgedCount human feedback confirmations.'
                      : 'No feedback submitted yet to calculate confirmed accuracy.',
                  style: TextStyle(
                    fontSize: 12,
                    color: isDark ? Colors.white60 : Colors.black54,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryGreen.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        '${stats.correctCount} Correct',
                        style: const TextStyle(color: AppTheme.primaryGreen, fontSize: 11, fontWeight: FontWeight.bold),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppTheme.warningColor.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        '${stats.incorrectCount} Misclassified',
                        style: const TextStyle(color: AppTheme.warningColor, fontSize: 11, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCategoryChartCard(SorterStats stats, bool isDark) {
    final categories = ['BIODEGRADABLE', 'PLASTIC', 'METAL', 'OTHER'];
    final total = stats.totalEvents;

    final sections = categories.asMap().entries.map((entry) {
      final idx = entry.key;
      final cat = entry.value;
      final count = stats.classCounts[cat] ?? 0;
      final isTouched = idx == _touchedIndex;
      final color = AppTheme.getCategoryColor(cat);
      final pct = total > 0 ? (count / total * 100) : 0.0;

      return PieChartSectionData(
        color: color,
        value: count.toDouble() > 0 ? count.toDouble() : 0.001,
        title: isTouched ? '${pct.toStringAsFixed(0)}%' : '',
        radius: isTouched ? 48 : 40,
        titleStyle: const TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
      );
    }).toList();

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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Waste Classification Breakdown',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const Icon(Icons.pie_chart_outline, size: 20, color: AppTheme.primaryGreen),
            ],
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              // Pie Chart
              SizedBox(
                height: 140,
                width: 140,
                child: PieChart(
                  PieChartData(
                    pieTouchData: PieTouchData(
                      touchCallback: (event, pieTouchResponse) {
                        setState(() {
                          if (!event.isInterestedForInteractions ||
                              pieTouchResponse == null ||
                              pieTouchResponse.touchedSection == null) {
                            _touchedIndex = -1;
                            return;
                          }
                          _touchedIndex = pieTouchResponse.touchedSection!.touchedSectionIndex;
                        });
                      },
                    ),
                    sectionsSpace: 3,
                    centerSpaceRadius: 30,
                    sections: sections,
                  ),
                ),
              ),
              const SizedBox(width: 20),
              // Category Legend & Counts
              Expanded(
                child: Column(
                  children: categories.map((cat) {
                    final count = stats.classCounts[cat] ?? 0;
                    final pct = total > 0 ? (count / total * 100) : 0.0;
                    final color = AppTheme.getCategoryColor(cat);
                    final icon = AppTheme.getCategoryIcon(cat);

                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        children: [
                          Icon(icon, color: color, size: 16),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              cat,
                              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          Text(
                            '$count (${pct.toStringAsFixed(0)}%)',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: isDark ? Colors.white70 : Colors.black87,
                            ),
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildHardwarePerformanceCard(SorterStats stats, bool isDark) {
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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Performance & Latency',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const Icon(Icons.speed, size: 20, color: AppTheme.accentCyan),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _latencyItem(
                  'AI Inference',
                  '${stats.avgInferenceTimeMs.toStringAsFixed(1)} ms',
                  'TFLite on Pi CPU',
                  AppTheme.accentCyan,
                  isDark,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _latencyItem(
                  'Mechanical Cycle',
                  '${(stats.avgSortingTimeMs / 1000).toStringAsFixed(2)} s',
                  'Stepper + Servo Drop',
                  AppTheme.metalColor,
                  isDark,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _latencyItem(String title, String val, String subtitle, Color color, bool isDark) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isDark ? AppTheme.darkCard : const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: TextStyle(fontSize: 11, color: isDark ? Colors.white60 : Colors.black54)),
          const SizedBox(height: 4),
          Text(val, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
          const SizedBox(height: 2),
          Text(subtitle, style: TextStyle(fontSize: 10, color: isDark ? Colors.white38 : Colors.black38)),
        ],
      ),
    );
  }

  Widget _buildBinDistributionCard(SorterStats stats, bool isDark) {
    final categories = ['BIODEGRADABLE', 'PLASTIC', 'METAL', 'OTHER'];
    final total = stats.totalEvents;

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
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Bin Load Distribution',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const SizedBox(height: 16),
          ...categories.map((cat) {
            final count = stats.binCounts[cat] ?? 0;
            final pct = total > 0 ? (count / total) : 0.0;
            final color = AppTheme.getCategoryColor(cat);

            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(cat, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                      Text(
                        '$count items (${(pct * 100).toStringAsFixed(0)}%)',
                        style: TextStyle(
                          fontSize: 12,
                          color: isDark ? Colors.white70 : Colors.black87,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: pct,
                      minHeight: 8,
                      backgroundColor: isDark ? AppTheme.darkCard : const Color(0xFFE2E8F0),
                      valueColor: AlwaysStoppedAnimation<Color>(color),
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}
