import 'package:flutter/material.dart';

import '../models/sorting_event.dart';
import '../services/firebase_service.dart';
import '../widgets/common_widgets.dart';

class DashboardScreen extends StatelessWidget {
  final FirebaseService firebase;

  const DashboardScreen({super.key, required this.firebase});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // --- Pi Status Card ---
        StreamBuilder<Map<String, dynamic>?>(
          stream: firebase.statusStream(),
          builder: (context, snap) {
            final data = snap.data;
            if (data == null) {
              return const _StatusCard(
                online: false,
                state: 'OFFLINE',
              );
            }
            final state = data['state']?.toString() ?? 'OFFLINE';
            final online = data['state'] != null;
            final position = data['current_position']?.toString() ?? 'UNKNOWN';
            final detected = data['last_detected_class']?.toString();
            final confidence = data['confidence'];
            final confStr = confidence is num
                ? '${(confidence * 100).toStringAsFixed(1)}%'
                : '—';
            final model = data['model_version']?.toString();

            return _StatusCard(
              online: online,
              state: state,
              position: position,
              detected: detected,
              confidence: confStr,
              model: model,
            );
          },
        ),
        const SizedBox(height: 16),

        // --- Quick Action ---
        FilledButton.tonalIcon(
          onPressed: () => firebase.requestHome(),
          icon: const Icon(Icons.home),
          label: const Text('Request carousel homing'),
        ),
        const SizedBox(height: 24),

        // --- Bin Status ---
        Text('Bin status', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 8),
        StreamBuilder<Map<String, dynamic>?>(
          stream: firebase.binsStream(),
          builder: (context, snap) {
            final bins = snap.data ?? {};
            if (bins.isEmpty) {
              return const Padding(
                padding: EdgeInsets.all(12),
                child: Text('No bin data yet.'),
              );
            }
            return Column(
              children: bins.entries.map((e) {
                final val = e.value;
                final dist = val is Map<String, dynamic>
                    ? val['distance_cm']
                    : null;
                final distNum = dist is num ? dist.toDouble() : null;
                return BinCard(
                  category: e.key,
                  distanceCm: distNum,
                );
              }).toList(),
            );
          },
        ),
        const SizedBox(height: 24),

        // --- Latest Event Preview ---
        Text(
          'Latest sorting',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 8),
        StreamBuilder<List<SortingEvent>>(
          stream: firebase.eventsStream(),
          builder: (context, snap) {
            final events = snap.data ?? [];
            if (events.isEmpty) {
              return const EmptyState(
                icon: Icons.inbox,
                title: 'No events yet',
                subtitle: 'Sorting events will appear here as items are processed.',
              );
            }
            // Show only the latest 5
            return Column(
              children: events.take(5).map((e) => EventCard(
                event: e,
                firebase: firebase,
                onFeedbackSubmitted: () {},
              )).toList(),
            );
          },
        ),
      ],
    );
  }
}

class _StatusCard extends StatelessWidget {
  final bool online;
  final String state;
  final String? position;
  final String? detected;
  final String? confidence;
  final String? model;

  const _StatusCard({
    required this.online,
    required this.state,
    this.position,
    this.detected,
    this.confidence,
    this.model,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      color: online ? Colors.green.shade50 : Colors.orange.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  online ? 'Pi online' : 'Pi offline',
                  style: theme.textTheme.titleLarge,
                ),
                const Spacer(),
                StatusIndicator(online: online, label: ''),
              ],
            ),
            const SizedBox(height: 4),
            Text('State: $state  •  Position: ${position ?? "UNKNOWN"}'),
            if (detected != null)
              Text('Last: $detected  •  Confidence: $confidence'),
            if (model != null)
              Text('Model: $model'),
          ],
        ),
      ),
    );
  }
}