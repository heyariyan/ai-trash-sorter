import 'package:flutter/material.dart';

import '../models/sorting_event.dart';
import '../services/firebase_service.dart';

class EventCard extends StatelessWidget {
  final SortingEvent event;
  final FirebaseService firebase;
  final VoidCallback onFeedbackSubmitted;

  const EventCard({
    super.key,
    required this.event,
    required this.firebase,
    required this.onFeedbackSubmitted,
  });

  Future<String?> _imageUrl() => firebase.imageDownloadUrl(event.imageStoragePath);

  Future<void> _submitCorrect(BuildContext context) async {
    await firebase.submitFeedback(eventId: event.eventId, status: 'correct');
    onFeedbackSubmitted();
  }

  Future<void> _chooseCorrection(BuildContext context) async {
    const bins = ['BIODEGRADABLE', 'PLASTIC', 'METAL', 'OTHER'];
    final selected = await showModalBottomSheet<String>(
      context: context,
      builder: (_) => SafeArea(
        child: Wrap(
          children: [
            const ListTile(title: Text('Select the correct bin')),
            ...bins.map(
              (bin) => ListTile(
                title: Text(bin),
                onTap: () => Navigator.pop(context, bin),
              ),
            ),
          ],
        ),
      ),
    );
    if (selected != null && context.mounted) {
      await firebase.submitFeedback(
        eventId: event.eventId,
        status: 'incorrect',
        correctedCategory: selected,
      );
      onFeedbackSubmitted();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isSuccess = event.success;
    final label = event.detectedClass ?? 'FAILED';
    final bin = event.selectedBin ?? '—';
    final confidence = event.confidence != null
        ? (event.confidence! * 100).toStringAsFixed(1) + '%'
        : '—';
    final time = event.timestamp ?? '—';

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Image preview
            if (event.imageStoragePath != null && event.imageStoragePath!.isNotEmpty)
              FutureBuilder<String?>(
                future: _imageUrl(),
                builder: (_, snap) => snap.hasData
                    ? Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.network(
                            snap.data!,
                            height: 140,
                            width: double.infinity,
                            fit: BoxFit.cover,
                            loadingBuilder: (_, child, progress) =>
                                progress == null
                                    ? child
                                    : const SizedBox(
                                        height: 140,
                                        child: Center(child: CircularProgressIndicator()),
                                      ),
                          ),
                        ),
                      )
                    : const SizedBox.shrink(),
              ),
            // Main info row
            Row(
              children: [
                Icon(
                  isSuccess ? Icons.check_circle : Icons.error,
                  color: isSuccess ? Colors.green : Colors.red,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Text(
                  '$label → $bin',
                  style: theme.textTheme.titleMedium?.copyWith(
                    color: isSuccess ? null : Colors.red,
                  ),
                ),
              ],
            ),
            // Metadata
            Text('$confidence  •  $time', style: theme.textTheme.bodySmall),
            Text(
              'Feedback: ${event.feedbackStatus}  •  Image: ${event.imageState}',
              style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey[700]),
            ),
            // Feedback buttons
            if (event.feedbackStatus == 'pending' && isSuccess) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: [
                  TextButton(
                    onPressed: () => _submitCorrect(context),
                    child: const Text('AI was correct'),
                  ),
                  FilledButton.tonal(
                    onPressed: () => _chooseCorrection(context),
                    child: const Text('Prediction incorrect'),
                  ),
                ],
              ),
            ],
            if (event.feedbackStatus == 'incorrect') ...[
              const SizedBox(height: 4),
              Text(
                'Corrected: ${event.correctedCategory ?? '—'}',
                style: theme.textTheme.bodySmall?.copyWith(color: Colors.orange),
              ),
            ],
            if (!isSuccess && event.failureStage != null) ...[
              const SizedBox(height: 4),
              Text(
                'Failure: ${event.failureStage} — ${event.error}',
                style: theme.textTheme.bodySmall?.copyWith(color: Colors.red),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class BinCard extends StatelessWidget {
  final String category;
  final double? distanceCm;

  const BinCard({super.key, required this.category, this.distanceCm});

  @override
  Widget build(BuildContext context) {
    final dist = distanceCm != null ? '${distanceCm!.toStringAsFixed(1)} cm' : 'N/A';
    return Card(
      child: ListTile(
        title: Text(category),
        trailing: Text(dist, style: const TextStyle(fontFamily: 'monospace')),
      ),
    );
  }
}

class StatusIndicator extends StatelessWidget {
  final bool online;
  final String label;

  const StatusIndicator({super.key, required this.online, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(
            color: online ? Colors.green : Colors.orange,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 6),
        Text(label, style: Theme.of(context).textTheme.bodyMedium),
      ],
    );
  }
}

class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Widget? action;

  const EmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.subtitle,
    this.action,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(title, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(subtitle, textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.grey[600])),
            if (action != null) ...[
              const SizedBox(height: 16),
              action!,
            ],
          ],
        ),
      ),
    );
  }
}