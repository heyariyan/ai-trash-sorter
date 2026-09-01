import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_database/firebase_database.dart';
import 'package:firebase_storage/firebase_storage.dart';

import '../models/sorting_event.dart';

// Centralized Realtime Database access for the Flutter app.
//
// The Pi is the sole authority on GPIO, motors, and sorting.
// The app only *reads* device state and *writes* feedback.
class FirebaseService {
  final DatabaseReference _db;
  final FirebaseStorage _storage;
  final String _deviceId;

  FirebaseService({
    required String deviceId,
    DatabaseReference? db,
    FirebaseStorage? storage,
  })  : _deviceId = deviceId,
        _db = db ?? FirebaseDatabase.instance.ref(),
        _storage = storage ?? FirebaseStorage.instance;

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

  Future<void> signOut() => FirebaseAuth.instance.signOut();

  // ---------------------------------------------------------
  // Device state
  // ---------------------------------------------------------
  DatabaseReference get _deviceRef => _db.child('devices/$_deviceId');

  DatabaseReference get _statusRef => _deviceRef.child('status');
  DatabaseReference get _binsRef => _deviceRef.child('bins');
  DatabaseReference get _eventsRef => _deviceRef.child('events');
  DatabaseReference get _feedbackRef => _deviceRef.child('feedback');
  DatabaseReference get _commandsRef => _deviceRef.child('commands');

  Stream<Map<String, dynamic>?> statusStream() =>
      _statusRef.onValue.map((e) {
        final v = e.snapshot.value;
        return v is Map<String, dynamic> ? v : null;
      });

  Stream<Map<String, dynamic>?> binsStream() =>
      _binsRef.onValue.map((e) {
        final v = e.snapshot.value;
        return v is Map<String, dynamic> ? v : {};
      });

  Stream<List<SortingEvent>> eventsStream() =>
      _eventsRef.onValue.map((e) {
        final value = e.snapshot.value;
        final map = value is Map<String, dynamic>
            ? Map<String, dynamic>.from(value)
            : <String, dynamic>{};
        return map.entries
            .map((entry) => SortingEvent.fromMap(entry.key, entry.value))
            .toList()
          ..sort((a, b) => (b.timestamp ?? '').compareTo(a.timestamp ?? ''));
      });

  // ---------------------------------------------------------
  // Actions
  // ---------------------------------------------------------
  Future<void> requestHome() => _commandsRef.child('calibrate').set({
        'requested': true,
        'requested_by': currentUser?.uid,
        'requested_at': ServerValue.timestamp,
      });

  Future<void> submitFeedback({
    required String eventId,
    required String status, // 'correct' | 'incorrect'
    String? correctedCategory,
  }) async {
    final eventData = <String, dynamic>{
      'status': status,
      'submitted_by': currentUser?.uid,
      'submitted_at': ServerValue.timestamp,
    };
    if (status == 'incorrect' && correctedCategory != null) {
      eventData['corrected_category'] = correctedCategory;
    }
    await _feedbackRef.child(eventId).set(eventData);
  }

  // ---------------------------------------------------------
  // Image helper
  // ---------------------------------------------------------
  Future<String?> imageDownloadUrl(String? path) async {
    if (path == null || path.isEmpty) return null;
    try {
      return await _storage.ref(path).getDownloadURL();
    } catch (_) {
      return null;
    }
  }
}

// Helper that mirrors [firebase_admin] `ServerValue.timestamp` for
// the Flutter side.  The Realtime Database understands the
// `{".sv": "timestamp"}` sentinel.
class ServerValue {
  static const Map<String, dynamic> timestamp = {'.sv': 'timestamp'};
}
