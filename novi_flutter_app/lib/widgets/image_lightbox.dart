import 'package:flutter/material.dart';
import '../models/sorting_event.dart';
import '../theme/app_theme.dart';

class ImageLightboxDialog extends StatelessWidget {
  final String imageUrl;
  final SortingEvent event;

  const ImageLightboxDialog({
    super.key,
    required this.imageUrl,
    required this.event,
  });

  static void show(BuildContext context, String imageUrl, SortingEvent event) {
    showDialog(
      context: context,
      barrierColor: Colors.black87,
      builder: (_) => ImageLightboxDialog(imageUrl: imageUrl, event: event),
    );
  }

  @override
  Widget build(BuildContext context) {
    final catColor = AppTheme.getCategoryColor(event.detectedClass);

    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.all(16),
      child: Stack(
        alignment: Alignment.center,
        children: [
          Container(
            constraints: const BoxConstraints(maxWidth: 700, maxHeight: 800),
            decoration: BoxDecoration(
              color: AppTheme.darkSurface,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppTheme.darkBorder),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Header
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: catColor.withValues(alpha: 0.2),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              event.detectedClass ?? 'UNKNOWN',
                              style: TextStyle(
                                color: catColor,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            event.confidencePercent,
                            style: const TextStyle(
                              color: Colors.white70,
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                      IconButton(
                        onPressed: () => Navigator.of(context).pop(),
                        icon: const Icon(Icons.close, color: Colors.white70),
                      ),
                    ],
                  ),
                ),
                const Divider(height: 1, color: AppTheme.darkBorder),
                // Image viewer
                Expanded(
                  child: InteractiveViewer(
                    minScale: 0.8,
                    maxScale: 4.0,
                    child: Center(
                      child: Image.network(
                        imageUrl,
                        fit: BoxFit.contain,
                        loadingBuilder: (_, child, progress) {
                          if (progress == null) return child;
                          return const Center(
                            child: CircularProgressIndicator(color: AppTheme.primaryGreen),
                          );
                        },
                        errorBuilder: (context, error, stackTrace) => const Center(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.broken_image, color: Colors.white38, size: 48),
                              SizedBox(height: 8),
                              Text('Image unavailable', style: TextStyle(color: Colors.white54)),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
                const Divider(height: 1, color: AppTheme.darkBorder),
                // Footer Telemetry
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _telemetryItem('Inference', '${event.inferenceTimeMs?.toStringAsFixed(1) ?? "—"} ms'),
                          _telemetryItem('Cycle Time', '${event.sortingTimeMs?.toStringAsFixed(0) ?? "—"} ms'),
                          _telemetryItem('Steps', '${event.movementSteps ?? 0}'),
                          _telemetryItem('Bin Clearance', '${event.binDistanceCm?.toStringAsFixed(1) ?? "—"} cm'),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Event ID: ${event.eventId} • ${event.formattedTime}',
                        style: const TextStyle(color: Colors.white38, fontSize: 11),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _telemetryItem(String label, String value) {
    return Column(
      children: [
        Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(color: Colors.white54, fontSize: 11)),
      ],
    );
  }
}
