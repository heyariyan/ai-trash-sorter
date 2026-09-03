import 'package:flutter/material.dart';
import '../models/sorting_event.dart';
import '../services/firebase_service.dart';
import '../theme/app_theme.dart';
import 'image_lightbox.dart';

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
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Feedback saved: AI prediction was verified correct'),
          backgroundColor: AppTheme.primaryGreenDark,
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  Future<void> _chooseCorrection(BuildContext context) async {
    const bins = ['BIODEGRADABLE', 'PLASTIC', 'METAL', 'OTHER'];
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final selected = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: isDark ? AppTheme.darkSurface : Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                child: Text(
                  'Select Actual Trash Category',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
              ),
              const Divider(),
              ...bins.map(
                (bin) {
                  final catColor = AppTheme.getCategoryColor(bin);
                  final catIcon = AppTheme.getCategoryIcon(bin);
                  return ListTile(
                    leading: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: catColor.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Icon(catIcon, color: catColor, size: 20),
                    ),
                    title: Text(
                      bin,
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: isDark ? Colors.white : Colors.black87,
                      ),
                    ),
                    trailing: const Icon(Icons.chevron_right, size: 18),
                    onTap: () => Navigator.pop(context, bin),
                  );
                },
              ),
            ],
          ),
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
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Feedback saved: Corrected to $selected'),
            backgroundColor: AppTheme.warningColor,
            duration: const Duration(seconds: 2),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final catColor = AppTheme.getCategoryColor(event.detectedClass);
    final catIcon = AppTheme.getCategoryIcon(event.detectedClass);
    final isSuccess = event.success;

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 6),
      decoration: BoxDecoration(
        color: isDark ? AppTheme.darkSurface : Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isDark ? AppTheme.darkBorder.withValues(alpha: 0.5) : const Color(0xFFE2E8F0),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top Row: Category + Confidence + Time
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: catColor.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(catIcon, color: catColor, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Flexible(
                            child: Text(
                              event.detectedClass ?? 'UNKNOWN OBJECT',
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                                letterSpacing: 0.3,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Icon(
                            Icons.arrow_forward_rounded,
                            size: 14,
                            color: isDark ? Colors.white38 : Colors.black38,
                          ),
                          const SizedBox(width: 6),
                          Flexible(
                            child: Text(
                              event.selectedBin ?? '—',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                                color: catColor,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${event.confidencePercent} confidence • ${event.relativeTime}',
                        style: TextStyle(
                          fontSize: 12,
                          color: isDark ? Colors.white54 : Colors.black54,
                        ),
                      ),
                    ],
                  ),
                ),
                // Success / Error status chip
                if (!isSuccess)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.errorColor.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.error_outline, color: AppTheme.errorColor, size: 14),
                        SizedBox(width: 4),
                        Text(
                          'FAILED',
                          style: TextStyle(
                            color: AppTheme.errorColor,
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),

            // Optional Image Preview Row
            if (event.imageStoragePath != null && event.imageStoragePath!.isNotEmpty) ...[
              const SizedBox(height: 12),
              FutureBuilder<String?>(
                future: _imageUrl(),
                builder: (context, snap) {
                  if (snap.connectionState == ConnectionState.waiting) {
                    return Container(
                      height: 120,
                      decoration: BoxDecoration(
                        color: isDark ? AppTheme.darkCard : const Color(0xFFF1F5F9),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Center(
                        child: CircularProgressIndicator(strokeWidth: 2, color: AppTheme.primaryGreen),
                      ),
                    );
                  }
                  final url = snap.data;
                  if (url == null) return const SizedBox.shrink();

                  return GestureDetector(
                    onTap: () => ImageLightboxDialog.show(context, url, event),
                    child: Stack(
                      children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: Image.network(
                            url,
                            height: 130,
                            width: double.infinity,
                            fit: BoxFit.cover,
                          ),
                        ),
                        Positioned(
                          right: 8,
                          bottom: 8,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: Colors.black.withValues(alpha: 0.75),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: const Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.fullscreen, color: Colors.white, size: 14),
                                SizedBox(width: 4),
                                Text(
                                  'Tap to zoom',
                                  style: TextStyle(color: Colors.white, fontSize: 10),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ],

            const SizedBox(height: 12),

            // Telemetry Tags
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                if (event.inferenceTimeMs != null)
                  _tag('⚡ ${event.inferenceTimeMs!.toStringAsFixed(0)}ms AI', isDark),
                if (event.movementSteps != null && event.movementSteps! > 0)
                  _tag('🔄 ${event.movementSteps} steps', isDark),
                if (event.binDistanceCm != null)
                  _tag('📏 ${event.binDistanceCm!.toStringAsFixed(1)}cm bin', isDark),
              ],
            ),

            // Feedback Controls / Badges
            const SizedBox(height: 12),
            if (event.feedbackStatus == 'pending' && isSuccess)
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _submitCorrect(context),
                      icon: const Icon(Icons.check_circle_outline, size: 16, color: AppTheme.primaryGreen),
                      label: const Text('Verified Correct'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppTheme.primaryGreen,
                        side: const BorderSide(color: AppTheme.primaryGreen),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _chooseCorrection(context),
                      icon: const Icon(Icons.edit_outlined, size: 16, color: AppTheme.warningColor),
                      label: const Text('Correct AI'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppTheme.warningColor,
                        side: const BorderSide(color: AppTheme.warningColor),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        padding: const EdgeInsets.symmetric(vertical: 10),
                      ),
                    ),
                  ),
                ],
              )
            else if (event.feedbackStatus == 'correct')
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: AppTheme.primaryGreen.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.verified, color: AppTheme.primaryGreen, size: 16),
                    SizedBox(width: 6),
                    Text(
                      'AI Classification Verified Correct',
                      style: TextStyle(
                        color: AppTheme.primaryGreen,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              )
            else if (event.feedbackStatus == 'incorrect')
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: AppTheme.warningColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.replay, color: AppTheme.warningColor, size: 16),
                    const SizedBox(width: 6),
                    Text(
                      'Corrected to: ${event.correctedCategory ?? "Manual override"}',
                      style: const TextStyle(
                        color: AppTheme.warningColor,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),

            if (!isSuccess && event.failureStage != null) ...[
              const SizedBox(height: 8),
              Text(
                'Stage: ${event.failureStage} • ${event.error ?? "Mechanism error"}',
                style: const TextStyle(color: AppTheme.errorColor, fontSize: 11),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _tag(String text, bool isDark) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: isDark ? AppTheme.darkCard : const Color(0xFFF1F5F9),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w500,
          color: isDark ? Colors.white70 : Colors.black87,
        ),
      ),
    );
  }
}
