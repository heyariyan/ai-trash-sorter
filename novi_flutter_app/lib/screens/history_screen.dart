import 'package:flutter/material.dart';

import '../models/sorting_event.dart';
import '../services/firebase_service.dart';
import '../widgets/common_widgets.dart';

class HistoryScreen extends StatelessWidget {
  final FirebaseService firebase;

  const HistoryScreen({super.key, required this.firebase});

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<List<SortingEvent>>(
      stream: firebase.eventsStream(),
      builder: (context, snap) {
        final events = snap.data;
        if (events == null || events.isEmpty) {
          return const EmptyState(
            icon: Icons.history,
            title: 'No sorting history',
            subtitle: 'Events will appear here as the Pi processes objects.',
          );
        }

        return Column(
          children: [
            // Filter chips
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  Text(
                    '${events.length} events',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const Spacer(),
                  TextButton(
                    onPressed: () {},
                    child: const Text('Export'),
                  ),
                ],
              ),
            ),
            // List
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                itemCount: events.length,
                itemBuilder: (_, i) => EventCard(
                  event: events[i],
                  firebase: firebase,
                  onFeedbackSubmitted: () {},
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}