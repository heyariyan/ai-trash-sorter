import 'dart:async';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_database/firebase_database.dart';
import 'package:firebase_storage/firebase_storage.dart';
import 'package:flutter/foundation.dart';

import '../models/sorting_event.dart';

class FirebaseService {
  final DatabaseReference _db;
  final FirebaseStorage _storage;
  final String _deviceId;
  bool demoMode = false;

  final _demoStatusCtrl = StreamController<DeviceStatus>.broadcast();
  final _demoBinsCtrl = StreamController<Map<String, BinStatus>>.broadcast();
  final _demoEventsCtrl = StreamController<List<SortingEvent>>.broadcast();
  List<SortingEvent> _mockEvents = [];
  Timer? _demoTimer;

  FirebaseService({
    required String deviceId,
    DatabaseReference? db,
    FirebaseStorage? storage,
  })  : _deviceId = deviceId,
        _db = db ??
            FirebaseDatabase.instanceFor(
              app: Firebase.app(),
              databaseURL:
                  'https://trash2444-default-rtdb.asia-southeast1.firebasedatabase.app',
            ).ref(),
        _storage = storage ?? FirebaseStorage.instance {
    _initMockData();
  }

  void _initMockData() {
    _mockEvents = [
      SortingEvent(
        eventId: 'evt-demo-101',
        detectedClass: 'PLASTIC',
        selectedBin: 'PLASTIC',
        confidence: 0.964,
        timestamp: DateTime.now().subtract(const Duration(minutes: 2)).toIso8601String(),
        modelVersion: 'v1.4-mobilenetv2',
        inferenceTimeMs: 48.2,
        sortingTimeMs: 1420.0,
        movementSteps: 50,
        movementDirection: 1,
        binDistanceCm: 18.5,
        feedbackStatus: 'correct',
        success: true,
      ),
      SortingEvent(
        eventId: 'evt-demo-102',
        detectedClass: 'BIODEGRADABLE',
        selectedBin: 'BIODEGRADABLE',
        confidence: 0.982,
        timestamp: DateTime.now().subtract(const Duration(minutes: 7)).toIso8601String(),
        modelVersion: 'v1.4-mobilenetv2',
        inferenceTimeMs: 44.1,
        sortingTimeMs: 1100.0,
        movementSteps: 0,
        movementDirection: 0,
        binDistanceCm: 14.2,
        feedbackStatus: 'correct',
        success: true,
      ),
      SortingEvent(
        eventId: 'evt-demo-103',
        detectedClass: 'METAL',
        selectedBin: 'METAL',
        confidence: 0.895,
        timestamp: DateTime.now().subtract(const Duration(minutes: 15)).toIso8601String(),
        modelVersion: 'v1.4-mobilenetv2',
        inferenceTimeMs: 52.0,
        sortingTimeMs: 1890.0,
        movementSteps: 100,
        movementDirection: 1,
        binDistanceCm: 22.0,
        feedbackStatus: 'pending',
        success: true,
      ),
      SortingEvent(
        eventId: 'evt-demo-104',
        detectedClass: 'OTHER',
        selectedBin: 'OTHER',
        confidence: 0.763,
        timestamp: DateTime.now().subtract(const Duration(minutes: 32)).toIso8601String(),
        modelVersion: 'v1.4-mobilenetv2',
        inferenceTimeMs: 58.7,
        sortingTimeMs: 2310.0,
        movementSteps: 150,
        movementDirection: 1,
        binDistanceCm: 24.8,
        feedbackStatus: 'incorrect',
        correctedCategory: 'PLASTIC',
        success: true,
      ),
      SortingEvent(
        eventId: 'evt-demo-105',
        detectedClass: 'BIODEGRADABLE',
        selectedBin: 'BIODEGRADABLE',
        confidence: 0.991,
        timestamp: DateTime.now().subtract(const Duration(hours: 1, minutes: 10)).toIso8601String(),
        modelVersion: 'v1.4-mobilenetv2',
        inferenceTimeMs: 42.5,
        sortingTimeMs: 1050.0,
        movementSteps: 0,
        movementDirection: 0,
        binDistanceCm: 15.0,
        feedbackStatus: 'correct',
        success: true,
      ),
    ];
  }

  void startDemoSimulation() {
    demoMode = true;
    _emitDemoState();
    _demoTimer?.cancel();
    _demoTimer = Timer.periodic(const Duration(seconds: 4), (timer) {
      _emitDemoState();
    });
  }

  void stopDemoSimulation() {
    demoMode = false;
    _demoTimer?.cancel();
  }

  void _emitDemoState() {
    final status = DeviceStatus(
      state: 'READY',
      currentPosition: 'BIODEGRADABLE',
      positionKnown: true,
      lastDetectedClass: 'PLASTIC',
      confidence: 0.964,
      modelVersion: 'v1.4-mobilenetv2',
      updatedAt: DateTime.now(),
      intakeDistanceCm: 18.2,
      binDistanceCm: 14.5,
      homeSensorActive: true,
      servoAngle: 0.0,
    );
    _demoStatusCtrl.add(status);

    _demoBinsCtrl.add({
      'BIODEGRADABLE': BinStatus(category: 'BIODEGRADABLE', distanceCm: 14.2, updatedAt: DateTime.now()),
      'PLASTIC': BinStatus(category: 'PLASTIC', distanceCm: 18.5, updatedAt: DateTime.now()),
      'METAL': BinStatus(category: 'METAL', distanceCm: 22.0, updatedAt: DateTime.now()),
      'OTHER': BinStatus(category: 'OTHER', distanceCm: 24.8, updatedAt: DateTime.now()),
    });

    _demoEventsCtrl.add(List.unmodifiable(_mockEvents));
  }

  // ---------------------------------------------------------
  // Auth
  // ---------------------------------------------------------
  User? get currentUser => FirebaseAuth.instance.currentUser;
  bool get isAuthenticated => currentUser != null;

  Future<UserCredential> signIn(String email, String password) =>
      FirebaseAuth.instance.signInWithEmailAndPassword(
        email: email,
        password: password,
      );

  Future<UserCredential> signInAnonymously() =>
      FirebaseAuth.instance.signInAnonymously();

  Future<void> signOut() => FirebaseAuth.instance.signOut();

  // ---------------------------------------------------------
  // Device state streams
  // ---------------------------------------------------------
  DatabaseReference get _deviceRef => _db.child('devices/$_deviceId');
  DatabaseReference get _statusRef => _deviceRef.child('status');
  DatabaseReference get _binsRef => _deviceRef.child('bins');
  DatabaseReference get _eventsRef => _deviceRef.child('events');
  DatabaseReference get _feedbackRef => _deviceRef.child('feedback');
  DatabaseReference get _commandsRef => _deviceRef.child('commands');

  Stream<DeviceStatus> statusStream() {
    if (demoMode) return _demoStatusCtrl.stream;
    return _statusRef.onValue.map((e) {
      final v = e.snapshot.value;
      if (v is Map) {
        return DeviceStatus.fromMap(Map<dynamic, dynamic>.from(v));
      }
      return DeviceStatus.empty;
    }).handleError((error) {
      if (kDebugMode) print('statusStream error: $error');
      return DeviceStatus.empty;
    });
  }

  Stream<Map<String, BinStatus>> binsStream() {
    if (demoMode) return _demoBinsCtrl.stream;
    return _binsRef.onValue.map((e) {
      final v = e.snapshot.value;
      final result = <String, BinStatus>{};
      if (v is Map) {
        v.forEach((key, val) {
          if (val is Map) {
            result[key.toString()] = BinStatus.fromMap(
              key.toString(),
              Map<dynamic, dynamic>.from(val),
            );
          }
        });
      }
      return result;
    }).handleError((error) {
      if (kDebugMode) print('binsStream error: $error');
      return <String, BinStatus>{};
    });
  }

  Stream<List<SortingEvent>> eventsStream() {
    if (demoMode) return _demoEventsCtrl.stream;
    return _eventsRef.onValue.map((e) {
      final value = e.snapshot.value;
      if (value is Map) {
        final list = <SortingEvent>[];
        value.forEach((k, v) {
          if (v is Map) {
            list.add(SortingEvent.fromMap(
              k.toString(),
              Map<dynamic, dynamic>.from(v),
            ));
          }
        });
        list.sort((a, b) => (b.timestamp ?? '').compareTo(a.timestamp ?? ''));
        return list;
      }
      return <SortingEvent>[];
    }).handleError((error) {
      if (kDebugMode) print('eventsStream error: $error');
      return <SortingEvent>[];
    });
  }

  // ---------------------------------------------------------
  // Commands & Feedback
  // ---------------------------------------------------------
  Future<void> requestHome() async {
    if (demoMode) {
      _emitDemoState();
      return;
    }
    await _commandsRef.child('calibrate').set({
      'requested': true,
      'requested_by': currentUser?.uid ?? 'web-user',
      'requested_at': ServerValue.timestamp,
    });
  }

  Future<void> submitFeedback({
    required String eventId,
    required String status, // 'correct' | 'incorrect'
    String? correctedCategory,
  }) async {
    if (demoMode) {
      final idx = _mockEvents.indexWhere((e) => e.eventId == eventId);
      if (idx != -1) {
        final old = _mockEvents[idx];
        _mockEvents[idx] = SortingEvent(
          eventId: old.eventId,
          detectedClass: old.detectedClass,
          selectedBin: old.selectedBin,
          confidence: old.confidence,
          timestamp: old.timestamp,
          modelVersion: old.modelVersion,
          inferenceTimeMs: old.inferenceTimeMs,
          sortingTimeMs: old.sortingTimeMs,
          movementSteps: old.movementSteps,
          movementDirection: old.movementDirection,
          binDistanceCm: old.binDistanceCm,
          feedbackStatus: status,
          correctedCategory: correctedCategory,
          imageState: old.imageState,
          imageStoragePath: old.imageStoragePath,
          success: old.success,
          failureStage: old.failureStage,
          error: old.error,
        );
        _demoEventsCtrl.add(List.unmodifiable(_mockEvents));
      }
      return;
    }

    final eventData = <String, dynamic>{
      'status': status,
      'submitted_by': currentUser?.uid ?? 'web-user',
      'submitted_at': ServerValue.timestamp,
    };
    if (status == 'incorrect' && correctedCategory != null) {
      eventData['corrected_category'] = correctedCategory;
    }
    await _feedbackRef.child(eventId).set(eventData);

    // Also update the event document feedbackStatus
    final updateData = <String, dynamic>{
      'feedback_status': status,
    };
    if (correctedCategory != null) {
      updateData['corrected_category'] = correctedCategory;
    }
    await _eventsRef.child(eventId).update(updateData);
  }

  // ---------------------------------------------------------
  // Image URL helper
  // ---------------------------------------------------------
  Future<String?> imageDownloadUrl(String? path) async {
    if (path == null || path.isEmpty) return null;
    try {
      return await _storage.ref(path).getDownloadURL();
    } catch (_) {
      return null;
    }
  }

  void dispose() {
    _demoTimer?.cancel();
    _demoStatusCtrl.close();
    _demoBinsCtrl.close();
    _demoEventsCtrl.close();
  }
}
