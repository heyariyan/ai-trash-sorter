import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';

import 'firebase_options.dart';
import 'screens/nav_shell.dart';

const String deviceId = 'rpi-sorter-01'; // Must match device_id in Pi configuration.

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await Firebase.initializeApp(
      options: DefaultFirebaseOptions.currentPlatform,
    );
  } catch (e) {
    if (kDebugMode) {
      print('Firebase initialization fallback notice: $e');
    }
  }
  runApp(const NoviSorterApp());
}
