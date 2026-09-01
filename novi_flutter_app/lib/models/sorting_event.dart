// Data models for the Novi sorter app.
//
// These are plain Dart classes that mirror the Firebase Realtime Database
// JSON shape written by the Raspberry Pi.  The Pi is the source of truth;
// the app only reads and displays.

class DeviceStatus {
  final String state;
  final String? currentPosition;
  final bool positionKnown;
  final String? lastDetectedClass;
  final double? confidence;
  final String? modelVersion;
  final DateTime? updatedAt;

  const DeviceStatus({
    required this.state,
    this.currentPosition,
    this.positionKnown = false,
    this.lastDetectedClass,
    this.confidence,
    this.modelVersion,
    this.updatedAt,
  });

  bool get isOnline =>
      state == 'READY' ||
      state == 'WAITING_FOR_CLEAR' ||
      state == 'DETECTED' ||
      state == 'CAPTURING' ||
      state == 'CLASSIFYING' ||
      state == 'MOVING' ||
      state == 'DROPPING' ||
      state == 'MEASURING';

  bool get isBusy =>
      state != 'READY' && state != 'WAITING_FOR_CLEAR' && state != 'OFFLINE';

  factory DeviceStatus.fromMap(Map<String, dynamic> map) {
    return DeviceStatus(
      state: _str(map['state'], 'OFFLINE'),
      currentPosition: _str(map['current_position'], null),
      positionKnown: _bool(map['position_known'], false),
      lastDetectedClass: _str(map['last_detected_class'], null),
      confidence: _dbl(map['confidence'], null),
      modelVersion: _str(map['model_version'], null),
      updatedAt: _ts(map['updated_at']),
    );
  }

  static const empty = DeviceStatus(state: 'OFFLINE');
}

class BinStatus {
  final String category;
  final double? distanceCm;
  final DateTime? updatedAt;

  const BinStatus({required this.category, this.distanceCm, this.updatedAt});

  factory BinStatus.fromMap(String key, Map<String, dynamic> map) =>
      BinStatus(
        category: key,
        distanceCm: _dbl(map['distance_cm'], null),
        updatedAt: _ts(map['updated_at']),
      );
}

class SortingEvent {
  final String eventId;
  final String? detectedClass;
  final String? selectedBin;
  final double? confidence;
  final String? timestamp;
  final String? modelVersion;
  final double? inferenceTimeMs;
  final double? sortingTimeMs;
  final int? movementSteps;
  final int? movementDirection;
  final double? binDistanceCm;
  final String feedbackStatus; // pending, correct, incorrect, unavailable
  final String? correctedCategory;
  final String imageState; // temporary, retained, deleted, diagnostic, unavailable
  final String? imageStoragePath;
  final bool success;
  final String? failureStage;
  final String? error;

  const SortingEvent({
    required this.eventId,
    this.detectedClass,
    this.selectedBin,
    this.confidence,
    this.timestamp,
    this.modelVersion,
    this.inferenceTimeMs,
    this.sortingTimeMs,
    this.movementSteps,
    this.movementDirection,
    this.binDistanceCm,
    this.feedbackStatus = 'pending',
    this.correctedCategory,
    this.imageState = 'unavailable',
    this.imageStoragePath,
    this.success = true,
    this.failureStage,
    this.error,
  });

  factory SortingEvent.fromMap(String id, Map<String, dynamic> map) {
    return SortingEvent(
      eventId: id,
      detectedClass: _str(map['detected_class'], null),
      selectedBin: _str(map['selected_bin'], null),
      confidence: _dbl(map['confidence'], null),
      timestamp: _str(map['timestamp'], null),
      modelVersion: _str(map['model_version'], null),
      inferenceTimeMs: _dbl(map['inference_time_ms'], null),
      sortingTimeMs: _dbl(map['sorting_time_ms'], null),
      movementSteps: _int(map['movement_steps'], null),
      movementDirection: _int(map['movement_direction'], null),
      binDistanceCm: _dbl(map['bin_distance_cm'], null),
      feedbackStatus: _str(map['feedback_status'], 'pending'),
      correctedCategory: _str(map['corrected_category'], null),
      imageState: _str(map['image_state'], 'unavailable'),
      imageStoragePath: _str(map['image_storage_path'], null),
      success: _bool(map['success'], true),
      failureStage: _str(map['failure_stage'], null),
      error: _str(map['error'], null),
    );
  }
}

class SorterStats {
  final int totalEvents;
  final int correctCount;
  final int incorrectCount;
  final int pendingCount;
  final double accuracy;
  final Map<String, int> classCounts;
  final Map<String, int> binCounts;

  const SorterStats({
    this.totalEvents = 0,
    this.correctCount = 0,
    this.incorrectCount = 0,
    this.pendingCount = 0,
    this.accuracy = 0,
    this.classCounts = const {},
    this.binCounts = const {},
  });

  factory SorterStats.fromEvents(List<SortingEvent> events) {
    int correct = 0, incorrect = 0, pending = 0;
    final classCounts = <String, int>{};
    final binCounts = <String, int>{};
    for (final e in events) {
      if (e.feedbackStatus == 'correct') {
        correct++;
      } else if (e.feedbackStatus == 'incorrect') {
        incorrect++;
      } else if (e.feedbackStatus == 'pending') {
        pending++;
      }
      if (e.detectedClass != null) {
        classCounts[e.detectedClass!] = (classCounts[e.detectedClass!] ?? 0) + 1;
      }
      if (e.selectedBin != null) {
        binCounts[e.selectedBin!] = (binCounts[e.selectedBin!] ?? 0) + 1;
      }
    }
    final judged = correct + incorrect;
    return SorterStats(
      totalEvents: events.length,
      correctCount: correct,
      incorrectCount: incorrect,
      pendingCount: pending,
      accuracy: judged > 0 ? (correct / judged * 100) : 0,
      classCounts: classCounts,
      binCounts: binCounts,
    );
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

String _str(Object? v, String? fallback) =>
    v == null ? (fallback ?? '') : v.toString();

double? _dbl(Object? v, double? fallback) {
  if (v == null) return fallback;
  if (v is num) return v.toDouble();
  return double.tryParse(v.toString()) ?? fallback;
}

int? _int(Object? v, int? fallback) {
  if (v == null) return fallback;
  if (v is int) return v;
  if (v is num) return v.toInt();
  return int.tryParse(v.toString()) ?? fallback;
}

bool _bool(Object? v, bool fallback) {
  if (v == null) return fallback;
  if (v is bool) return v;
  if (v is num) return v != 0;
  if (v is String) return v.toLowerCase() == 'true';
  return fallback;
}

DateTime? _ts(Object? v) {
  if (v == null) return null;
  if (v is int) {
    return DateTime.fromMillisecondsSinceEpoch(v);
  }
  if (v is String) {
    return DateTime.tryParse(v);
  }
  return null;
}
