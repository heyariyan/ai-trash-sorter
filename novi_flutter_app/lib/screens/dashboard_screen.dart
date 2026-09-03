import 'package:flutter/material.dart';
import '../models/sorting_event.dart';
import '../services/firebase_service.dart';
import '../theme/app_theme.dart';
import '../widgets/bin_level_gauge.dart';
import '../widgets/carousel_visualizer.dart';
import '../widgets/common_widgets.dart';
import '../widgets/event_card.dart';

class DashboardScreen extends StatefulWidget {
  final FirebaseService firebase;

  const DashboardScreen({super.key, required this.firebase});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  bool _isHoming = false;

  Future<void> _triggerHome() async {
    setState(() => _isHoming = true);
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
            content: Text('Failed to trigger homing: $e'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isHoming = false);
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

        return StreamBuilder<Map<String, BinStatus>>(
          stream: widget.firebase.binsStream(),
          builder: (context, binsSnap) {
            final bins = binsSnap.data ?? {};

            return StreamBuilder<List<SortingEvent>>(
              stream: widget.firebase.eventsStream(),
              builder: (context, eventsSnap) {
                final events = eventsSnap.data ?? [];
                final stats = SorterStats.fromEvents(events);

                return Scaffold(
                  body: CustomScrollView(
                    slivers: [
                      // Sliver App Bar
                      SliverAppBar(
                        floating: true,
                        pinned: false,
                        backgroundColor: isDark ? AppTheme.darkBg : const Color(0xFFF8FAFC),
                        elevation: 0,
                        title: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: AppTheme.primaryGreen.withValues(alpha: 0.2),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: const Icon(Icons.delete_sweep, color: AppTheme.primaryGreen, size: 22),
                            ),
                            const SizedBox(width: 12),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Novi AI Dustbin',
                                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                                ),
                                Text(
                                  'Autonomous AI Trash Sorter',
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: isDark ? Colors.white60 : Colors.black54,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                        actions: [
                          Padding(
                            padding: const EdgeInsets.only(right: 16),
                            child: Center(
                              child: StatusBadge(
                                online: isOnline,
                                state: status.state,
                              ),
                            ),
                          ),
                        ],
                      ),

                      // Content Body
                      SliverPadding(
                        padding: const EdgeInsets.all(16),
                        sliver: SliverList(
                          delegate: SliverChildListDelegate([
                            // Live Hero Status Card
                            _buildHeroStatusCard(status, isDark),
                            const SizedBox(height: 16),

                            // Quick Actions Bar
                            _buildQuickActionsBar(status, isDark),
                            const SizedBox(height: 24),

                            // Key Stats Row
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
                                      icon: Icons.auto_awesome,
                                      color: AppTheme.accentCyan,
                                    ),
                                    MetricSummaryTile(
                                      label: 'AI Accuracy',
                                      value: '${stats.accuracy.toStringAsFixed(1)}%',
                                      icon: Icons.verified,
                                      color: AppTheme.primaryGreen,
                                      subtitle: '${stats.correctCount} verified',
                                    ),
                                    MetricSummaryTile(
                                      label: 'Avg AI Speed',
                                      value: '${stats.avgInferenceTimeMs.toStringAsFixed(0)}ms',
                                      icon: Icons.bolt,
                                      color: AppTheme.metalColor,
                                      subtitle: 'TFLite MobileNet',
                                    ),
                                    MetricSummaryTile(
                                      label: 'Avg Cycle Time',
                                      value: '${(stats.avgSortingTimeMs / 1000).toStringAsFixed(1)}s',
                                      icon: Icons.timer,
                                      color: AppTheme.otherColor,
                                      subtitle: 'Intake to Drop',
                                    ),
                                  ],
                                );
                              },
                            ),
                            const SizedBox(height: 24),

                            // Carousel & Bins Grid
                            LayoutBuilder(
                              builder: (context, constraints) {
                                if (constraints.maxWidth > 900) {
                                  return Row(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Expanded(
                                        flex: 5,
                                        child: CarouselVisualizer(
                                          currentPosition: status.currentPosition,
                                          state: status.state,
                                          positionKnown: status.positionKnown,
                                        ),
                                      ),
                                      const SizedBox(width: 16),
                                      Expanded(
                                        flex: 7,
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              'Bin Capacity Levels',
                                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                                    fontWeight: FontWeight.bold,
                                                  ),
                                            ),
                                            const SizedBox(height: 12),
                                            BinGaugesGrid(bins: bins),
                                          ],
                                        ),
                                      ),
                                    ],
                                  );
                                }

                                return Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    CarouselVisualizer(
                                      currentPosition: status.currentPosition,
                                      state: status.state,
                                      positionKnown: status.positionKnown,
                                    ),
                                    const SizedBox(height: 20),
                                    Text(
                                      'Bin Capacity Levels',
                                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                            fontWeight: FontWeight.bold,
                                          ),
                                    ),
                                    const SizedBox(height: 12),
                                    BinGaugesGrid(bins: bins),
                                  ],
                                );
                              },
                            ),
                            const SizedBox(height: 28),

                            // Live Activity Feed Header
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Row(
                                  children: [
                                    Container(
                                      width: 8,
                                      height: 8,
                                      decoration: const BoxDecoration(
                                        color: AppTheme.primaryGreen,
                                        shape: BoxShape.circle,
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    Text(
                                      'Live Sorting Activity',
                                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                                            fontWeight: FontWeight.bold,
                                          ),
                                    ),
                                  ],
                                ),
                                Text(
                                  'Showing latest 5',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: isDark ? Colors.white54 : Colors.black54,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),

                            // Recent Events List
                            if (events.isEmpty)
                              const EmptyStateWidget(
                                icon: Icons.inbox_outlined,
                                title: 'No waste sorted yet',
                                subtitle: 'Items placed in Novi will trigger real-time AI classification and sorting logs.',
                              )
                            else
                              ...events.take(5).map(
                                    (e) => EventCard(
                                      event: e,
                                      firebase: widget.firebase,
                                      onFeedbackSubmitted: () => setState(() {}),
                                    ),
                                  ),
                            const SizedBox(height: 40),
                          ]),
                        ),
                      ),
                    ],
                  ),
                );
              },
            );
          },
        );
      },
    );
  }

  Widget _buildHeroStatusCard(DeviceStatus status, bool isDark) {
    final isOnline = status.isOnline;
    final catColor = AppTheme.getCategoryColor(status.lastDetectedClass);

    return Container(
      padding: const EdgeInsets.all(20),
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
          color: isOnline
              ? AppTheme.primaryGreen.withValues(alpha: 0.3)
              : (isDark ? AppTheme.darkBorder.withValues(alpha: 0.5) : const Color(0xFFE2E8F0)),
        ),
        boxShadow: [
          BoxShadow(
            color: isOnline
                ? AppTheme.primaryGreen.withValues(alpha: 0.08)
                : Colors.black.withValues(alpha: 0.05),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 12,
                    height: 12,
                    decoration: BoxDecoration(
                      color: isOnline ? AppTheme.primaryGreen : Colors.grey,
                      shape: BoxShape.circle,
                      boxShadow: [
                        if (isOnline)
                          BoxShadow(
                            color: AppTheme.primaryGreen.withValues(alpha: 0.6),
                            blurRadius: 8,
                            spreadRadius: 2,
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    isOnline ? 'Raspberry Pi Connected' : 'Sorter Offline / Standby',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                      color: isOnline ? AppTheme.primaryGreen : (isDark ? Colors.white70 : Colors.black54),
                    ),
                  ),
                ],
              ),
              Text(
                'ID: rpi-sorter-01',
                style: TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 12,
                  color: isDark ? Colors.white54 : Colors.black54,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'CURRENT STATUS',
                      style: TextStyle(
                        fontSize: 11,
                        letterSpacing: 0.8,
                        fontWeight: FontWeight.w600,
                        color: isDark ? Colors.white54 : Colors.black54,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      status.state.isEmpty ? 'OFFLINE' : status.state,
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: isOnline ? AppTheme.primaryGreen : (isDark ? Colors.white : Colors.black87),
                      ),
                    ),
                  ],
                ),
              ),
              if (status.lastDetectedClass != null) ...[
                Container(
                  height: 36,
                  width: 1,
                  color: isDark ? AppTheme.darkBorder : const Color(0xFFCBD5E1),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'LAST DETECTED ITEM',
                        style: TextStyle(
                          fontSize: 11,
                          letterSpacing: 0.8,
                          fontWeight: FontWeight.w600,
                          color: isDark ? Colors.white54 : Colors.black54,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        status.lastDetectedClass!,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: catColor,
                        ),
                      ),
                      if (status.confidence != null)
                        Text(
                          '${(status.confidence! * 100).toStringAsFixed(1)}% confidence',
                          style: TextStyle(
                            fontSize: 11,
                            color: isDark ? Colors.white60 : Colors.black54,
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActionsBar(DeviceStatus status, bool isDark) {
    return Row(
      children: [
        Expanded(
          flex: 2,
          child: FilledButton.icon(
            onPressed: _isHoming ? null : _triggerHome,
            icon: _isHoming
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black),
                  )
                : const Icon(Icons.home_outlined, size: 18),
            label: Text(_isHoming ? 'Homing...' : 'Home Calibration'),
            style: FilledButton.styleFrom(
              backgroundColor: AppTheme.primaryGreen,
              foregroundColor: Colors.black,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          flex: 1,
          child: OutlinedButton.icon(
            onPressed: () {
              if (widget.firebase.demoMode) {
                widget.firebase.stopDemoSimulation();
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Switched to Live Firebase Mode')),
                );
              } else {
                widget.firebase.startDemoSimulation();
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Demo Simulation Mode Activated')),
                );
              }
              setState(() {});
            },
            icon: Icon(
              widget.firebase.demoMode ? Icons.stop_circle_outlined : Icons.play_circle_outline,
              size: 18,
              color: widget.firebase.demoMode ? AppTheme.warningColor : AppTheme.accentCyan,
            ),
            label: Text(widget.firebase.demoMode ? 'Live Mode' : 'Demo Mode'),
            style: OutlinedButton.styleFrom(
              foregroundColor: widget.firebase.demoMode ? AppTheme.warningColor : AppTheme.accentCyan,
              side: BorderSide(
                color: widget.firebase.demoMode ? AppTheme.warningColor : AppTheme.accentCyan,
              ),
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
          ),
        ),
      ],
    );
  }
}
