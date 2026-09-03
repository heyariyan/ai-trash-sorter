import 'package:flutter_test/flutter_test.dart';
import 'package:novi_flutter_app/models/sorting_event.dart';

void main() {
  group('DeviceStatus Model Tests', () {
    test('DeviceStatus fromMap handles valid data', () {
      final data = {
        'state': 'READY',
        'current_position': 'BIODEGRADABLE',
        'position_known': true,
        'last_detected_class': 'PLASTIC',
        'confidence': 0.95,
        'model_version': 'v1.4',
        'updated_at': DateTime.now().toIso8601String(),
      };
      final status = DeviceStatus.fromMap(data);
      expect(status.state, 'READY');
      expect(status.isOnline, true);
      expect(status.isReady, true);
      expect(status.isBusy, false);
      expect(status.currentPosition, 'BIODEGRADABLE');
    });

    test('DeviceStatus handles empty map with fallback', () {
      final status = DeviceStatus.fromMap({});
      expect(status.state, 'OFFLINE');
      expect(status.isOnline, false);
    });
  });

  group('BinStatus Model Tests', () {
    test('Calculates fill percentage correctly based on ultrasonic depth', () {
      // 28cm clearance = 0% full (empty)
      final emptyBin = BinStatus(category: 'PLASTIC', distanceCm: 28.0);
      expect(emptyBin.fillPercentage, closeTo(0.0, 0.05));
      expect(emptyBin.isNearFull, false);

      // 4cm clearance = 100% full
      final fullBin = BinStatus(category: 'METAL', distanceCm: 4.0);
      expect(fullBin.fillPercentage, closeTo(1.0, 0.05));
      expect(fullBin.isNearFull, true);

      // 16cm clearance = ~50% full
      final halfBin = BinStatus(category: 'OTHER', distanceCm: 16.0);
      expect(halfBin.fillPercentage, closeTo(0.5, 0.05));
    });
  });

  group('SortingEvent & SorterStats Tests', () {
    test('SorterStats accurately aggregates event metrics', () {
      final events = [
        const SortingEvent(
          eventId: '1',
          detectedClass: 'PLASTIC',
          selectedBin: 'PLASTIC',
          confidence: 0.92,
          feedbackStatus: 'correct',
          inferenceTimeMs: 50.0,
          sortingTimeMs: 1200.0,
        ),
        const SortingEvent(
          eventId: '2',
          detectedClass: 'BIODEGRADABLE',
          selectedBin: 'BIODEGRADABLE',
          confidence: 0.98,
          feedbackStatus: 'correct',
          inferenceTimeMs: 40.0,
          sortingTimeMs: 1000.0,
        ),
        const SortingEvent(
          eventId: '3',
          detectedClass: 'METAL',
          selectedBin: 'METAL',
          confidence: 0.85,
          feedbackStatus: 'incorrect',
          correctedCategory: 'OTHER',
          inferenceTimeMs: 60.0,
          sortingTimeMs: 1400.0,
        ),
      ];

      final stats = SorterStats.fromEvents(events);
      expect(stats.totalEvents, 3);
      expect(stats.correctCount, 2);
      expect(stats.incorrectCount, 1);
      expect(stats.accuracy, closeTo(66.67, 0.1));
      expect(stats.avgInferenceTimeMs, closeTo(50.0, 0.1));
      expect(stats.avgSortingTimeMs, closeTo(1200.0, 0.1));
      expect(stats.classCounts['PLASTIC'], 1);
      expect(stats.classCounts['BIODEGRADABLE'], 1);
      expect(stats.classCounts['METAL'], 1);
    });

    test('SorterStats generates valid CSV output', () {
      final events = [
        const SortingEvent(
          eventId: 'evt-001',
          timestamp: '2026-09-01T12:00:00Z',
          detectedClass: 'PLASTIC',
          selectedBin: 'PLASTIC',
          confidence: 0.95,
          success: true,
          feedbackStatus: 'correct',
        ),
      ];
      final csv = SorterStats.exportToCsv(events);
      expect(csv.contains('evt-001'), true);
      expect(csv.contains('PLASTIC'), true);
      expect(csv.contains('95.0'), true);
      expect(csv.contains('correct'), true);
    });
  });
}
