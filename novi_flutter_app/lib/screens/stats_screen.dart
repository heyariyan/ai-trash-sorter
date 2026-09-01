import 'package:flutter/material.dart';

import '../models/sorting_event.dart';
import '../services/firebase_service.dart';
import '../widgets/common_widgets.dart';

class StatsScreen extends StatelessWidget {
  final FirebaseService firebase;

  const StatsScreen({super.key, required this.firebase});

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<List<SortingEvent>>(
      stream: firebase.eventsStream(),
      builder: (context, snap) {
        final events = snap.data;
        if (events == null || events.isEmpty) {
          return const EmptyState(
            icon: Icons.bar_chart,
            title: 'No data yet',
            subtitle: 'Sorting statistics will appear here after events are recorded.',
          );
        }

        final stats = SorterStats.fromEvents(events);
        final theme = Theme.of(context);
        final classEntries = stats.classCounts.entries.toList()
          ..sort((a, b) => b.value.compareTo(a.value));
        final binEntries = stats.binCounts.entries.toList()
          ..sort((a, b) => b.value.compareTo(a.value));

        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // --- Overall Accuracy ---
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Text(
                      '${stats.accuracy.toStringAsFixed(1)}%',
                      style: theme.textTheme.displayMedium?.copyWith(
                        color: stats.accuracy >= 80
                            ? Colors.green
                            : stats.accuracy >= 50
                                ? Colors.orange
                                : Colors.red,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'AI Accuracy',
                      style: theme.textTheme.titleMedium,
                    ),
                    Text(
                      'Based on ${stats.correctCount} correct / '
                      '${stats.correctCount + stats.incorrectCount} judged',
                      style: theme.textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // --- Summary Cards ---
            Row(
              children: [
                _SummaryTile(label: 'Total', count: stats.totalEvents, color: Colors.blue),
                const SizedBox(width: 8),
                _SummaryTile(label: 'Correct', count: stats.correctCount, color: Colors.green),
                const SizedBox(width: 8),
                _SummaryTile(label: 'Incorrect', count: stats.incorrectCount, color: Colors.red),
                const SizedBox(width: 8),
                _SummaryTile(label: 'Pending', count: stats.pendingCount, color: Colors.orange),
              ],
            ),
            const SizedBox(height: 24),

            // --- Class Breakdown ---
            Text('Classification breakdown', style: theme.textTheme.titleLarge),
            const SizedBox(height: 8),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  children: classEntries.isEmpty
                      ? [const Text('No data')]
                      : classEntries.map((e) {
                          final pct = stats.totalEvents > 0
                              ? (e.value / stats.totalEvents * 100)
                              : 0.0;
                          return Padding(
                            padding: const EdgeInsets.symmetric(vertical: 4),
                            child: Row(
                              children: [
                                Expanded(child: Text(e.key)),
                                SizedBox(
                                  width: 100,
                                  child: LinearProgressIndicator(
                                    value: pct / 100,
                                    backgroundColor: Colors.grey[200],
                                  ),
                                ),
                                const SizedBox(width: 8),
                                SizedBox(
                                  width: 60,
                                  child: Text(
                                    '${e.value} ($pct)',
                                    textAlign: TextAlign.end,
                                    style: theme.textTheme.bodySmall,
                                  ),
                                ),
                              ],
                            ),
                          );
                        }).toList(),
                ),
              ),
            ),
            const SizedBox(height: 24),

            // --- Bin Breakdown ---
            Text('Bin distribution', style: theme.textTheme.titleLarge),
            const SizedBox(height: 8),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  children: binEntries.isEmpty
                      ? [const Text('No data')]
                      : binEntries.map((e) {
                          final pct = stats.totalEvents > 0
                              ? (e.value / stats.totalEvents * 100)
                              : 0.0;
                          return Padding(
                            padding: const EdgeInsets.symmetric(vertical: 4),
                            child: Row(
                              children: [
                                Expanded(child: Text(e.key)),
                                SizedBox(
                                  width: 100,
                                  child: LinearProgressIndicator(
                                    value: pct / 100,
                                    backgroundColor: Colors.grey[200],
                                  ),
                                ),
                                const SizedBox(width: 8),
                                SizedBox(
                                  width: 60,
                                  child: Text(
                                    '${e.value} ($pct)',
                                    textAlign: TextAlign.end,
                                    style: theme.textTheme.bodySmall,
                                  ),
                                ),
                              ],
                            ),
                          );
                        }).toList(),
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _SummaryTile extends StatelessWidget {
  final String label;
  final int count;
  final Color color;

  const _SummaryTile({
    required this.label,
    required this.count,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
          child: Column(
            children: [
              Text(
                '$count',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: color),
              ),
              const SizedBox(height: 4),
              Text(label, style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
        ),
      ),
    );
  }
}