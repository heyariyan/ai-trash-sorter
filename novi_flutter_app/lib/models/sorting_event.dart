import 'package:intl/intl.dart';

class DeviceStatus {
  final String state;
  final String? currentPosition;
  final bool positionKnown;
  final String? lastDetectedClass;
  final double? confidence;
  final String? modelVersion;
  final DateTime? updatedAt;
  final double? intakeDistanceCm;
  final double? binDistanceCm;
  final bool? homeSensorActive;
  final double? servoAngle;

  const DeviceStatus({
    required this.state,
    this.currentPosition,
    this.positionKnown = false,
    this.lastDetectedClass,
    this.confidence,
    this.modelVersion,
    this.updatedAt,
    this.intakeDistanceCm,
    this.binDistanceCm,
    this.homeSensorActive,
    this.servoAngle,
  });

  bool get isOnline {
    if (updatedAt != null) {
      final diff = DateTime.now().toUtc().difference(updatedAt!);
      if (diff.inSeconds > 45) return false;
    }
    return state != 'OFFLINE' && state.isNotEmpty;
  }

  bool get isReady => state.toUpperCase() == 'READY';
  bool get isBusy =>
      state.isNotEmpty &&
      state != 'READY' &&
      state != 'WAITING_FOR_CLEAR' &&
      state != 'OFFLINE' &&
      state != 'ERROR';
  bool get isError => state.toUpperCase() == 'ERROR';

  factory DeviceStatus.fromMap(Map<dynamic, dynamic> map) {
    return DeviceStatus(
      state: _str(map['state'], 'OFFLINE'),
      currentPosition: _str(map['current_position'], null),
      positionKnown: _bool(map['position_known'], false),
      lastDetectedClass: _str(map['last_detected_class'], null),
      confidence: _dbl(map['confidence'], null),
      modelVersion: _str(map['model_version'], null),
      updatedAt: _ts(map['updated_at']),
      intakeDistanceCm: _dbl(map['intake_distance_cm'], null),
      binDistanceCm: _dbl(map['bin_distance_cm'], null),
      homeSensorActive: _bool(map['home_sensor_active'], false),
      servoAngle: _dbl(map['servo_angle'], null),
    );
  }

  static const empty = DeviceStatus(state: 'OFFLINE');
}

class BinStatus {
  final String category;
  final double? distanceCm;
  final DateTime? updatedAt;

  const BinStatus({
    required this.category,
    this.distanceCm,
    this.updatedAt,
  });

  /// Capacity percentage (0.0 to 1.0)
  /// Sorter ultrasonic sensor: ~30cm = empty (0%), ~5cm = full (100%)
  double get fillPercentage {
    if (distanceCm == null) return 0.0;
    const maxEmptyDistance = 28.0; // cm
    const minFullDistance = 4.0; // cm
    final clamped = distanceCm!.clamp(minFullDistance, maxEmptyDistance);
    return 1.0 - ((clamped - minFullDistance) / (maxEmptyDistance - minFullDistance));
  }

  bool get isNearFull => fillPercentage >= 0.80;

  factory BinStatus.fromMap(String key, Map<dynamic, dynamic> map) => BinStatus(
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

  DateTime? get parsedTime {
    if (timestamp == null || timestamp!.isEmpty) return null;
    try {
      return DateTime.parse(timestamp!);
    } catch (_) {
      return null;
    }
  }

  String get formattedTime {
    final t = parsedTime;
    if (t == null) return timestamp ?? '—';
    return DateFormat('MMM d, h:mm:ss a').format(t.toLocal());
  }

  String get relativeTime {
    final t = parsedTime;
    if (t == null) return 'Just now';
    final now = DateTime.now();
    final diff = now.difference(t.toLocal());
    if (diff.inSeconds < 60) return '${diff.inSeconds}s ago';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }

  String get confidencePercent {
    if (confidence == null) return '—';
    return '${(confidence! * 100).toStringAsFixed(1)}%';
  }

  factory SortingEvent.fromMap(String id, Map<dynamic, dynamic> map) {
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

  Map<String, dynamic> toMap() => {
        'eventId': eventId,
        'detectedClass': detectedClass,
        'selectedBin': selectedBin,
        'confidence': confidence,
        'timestamp': timestamp,
        'modelVersion': modelVersion,
        'inferenceTimeMs': inferenceTimeMs,
        'sortingTimeMs': sortingTimeMs,
        'movementSteps': movementSteps,
        'movementDirection': movementDirection,
        'binDistanceCm': binDistanceCm,
        'feedbackStatus': feedbackStatus,
        'correctedCategory': correctedCategory,
        'imageState': imageState,
        'imageStoragePath': imageStoragePath,
        'success': success,
        'failureStage': failureStage,
        'error': error,
      };
}

class SorterStats {
  final int totalEvents;
  final int correctCount;
  final int incorrectCount;
  final int pendingCount;
  final double accuracy;
  final double avgInferenceTimeMs;
  final double avgSortingTimeMs;
  final Map<String, int> classCounts;
  final Map<String, int> binCounts;

  const SorterStats({
    this.totalEvents = 0,
    this.correctCount = 0,
    this.incorrectCount = 0,
    this.pendingCount = 0,
    this.accuracy = 0,
    this.avgInferenceTimeMs = 0,
    this.avgSortingTimeMs = 0,
    this.classCounts = const {},
    this.binCounts = const {},
  });

  factory SorterStats.fromEvents(List<SortingEvent> events) {
    int correct = 0, incorrect = 0, pending = 0;
    double totalInfTime = 0;
    int infCount = 0;
    double totalSortTime = 0;
    int sortCount = 0;

    final classCounts = <String, int>{
      'BIODEGRADABLE': 0,
      'PLASTIC': 0,
      'METAL': 0,
      'OTHER': 0,
    };
    final binCounts = <String, int>{
      'BIODEGRADABLE': 0,
      'PLASTIC': 0,
      'METAL': 0,
      'OTHER': 0,
    };

    for (final e in events) {
      if (e.feedbackStatus == 'correct') {
        correct++;
      } else if (e.feedbackStatus == 'incorrect') {
        incorrect++;
      } else {
        pending++;
      }

      if (e.detectedClass != null) {
        final c = e.detectedClass!.toUpperCase();
        classCounts[c] = (classCounts[c] ?? 0) + 1;
      }
      if (e.selectedBin != null) {
        final b = e.selectedBin!.toUpperCase();
        binCounts[b] = (binCounts[b] ?? 0) + 1;
      }

      if (e.inferenceTimeMs != null && e.inferenceTimeMs! > 0) {
        totalInfTime += e.inferenceTimeMs!;
        infCount++;
      }
      if (e.sortingTimeMs != null && e.sortingTimeMs! > 0) {
        totalSortTime += e.sortingTimeMs!;
        sortCount++;
      }
    }

    final judged = correct + incorrect;
    return SorterStats(
      totalEvents: events.length,
      correctCount: correct,
      incorrectCount: incorrect,
      pendingCount: pending,
      accuracy: judged > 0 ? (correct / judged * 100) : 0,
      avgInferenceTimeMs: infCount > 0 ? (totalInfTime / infCount) : 0,
      avgSortingTimeMs: sortCount > 0 ? (totalSortTime / sortCount) : 0,
      classCounts: classCounts,
      binCounts: binCounts,
    );
  }

  static String exportToCsv(List<SortingEvent> events) {
    final buffer = StringBuffer();
    buffer.writeln(
        'Event ID,Timestamp,Detected Class,Selected Bin,Confidence,Success,Feedback Status,Corrected Category,Inference Time (ms),Sorting Time (ms),Movement Steps,Bin Distance (cm)');
    for (final e in events) {
      buffer.writeln([
        e.eventId,
        e.timestamp ?? '',
        e.detectedClass ?? '',
        e.selectedBin ?? '',
        e.confidence != null ? (e.confidence! * 100).toStringAsFixed(1) : '',
        e.success ? 'TRUE' : 'FALSE',
        e.feedbackStatus,
        e.correctedCategory ?? '',
        e.inferenceTimeMs?.toStringAsFixed(1) ?? '',
        e.sortingTimeMs?.toStringAsFixed(1) ?? '',
        e.movementSteps?.toString() ?? '',
        e.binDistanceCm?.toStringAsFixed(1) ?? '',
      ].map((field) => '"${field.replaceAll('"', '""')}"').join(','));
    }
    return buffer.toString();
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
  final s = v.toString().trim().toLowerCase();
  return s == 'true' || s == '1';
}

DateTime? _ts(Object? v) {
  if (v == null) return null;
  if (v is int) {
    return DateTime.fromMillisecondsSinceEpoch(v, isUtc: true);
  }
  if (v is String) {
    try {
      return DateTime.parse(v);
    } catch (_) {
      return null;
    }
  }
  return null;
}
