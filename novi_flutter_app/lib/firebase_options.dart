import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

/// Default [FirebaseOptions] for use with your Firebase apps.
class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) {
      return web;
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      case TargetPlatform.macOS:
        return macos;
      case TargetPlatform.windows:
        return windows;
      case TargetPlatform.linux:
        return web;
      default:
        return web;
    }
  }

  static const FirebaseOptions web = FirebaseOptions(
    apiKey: 'AIzaSyBWpujFV1iH0Q7xCI8DEvuTTxj6PRTbuBk',
    appId: '1:578841815881:web:2de019e6535cd8b4738898',
    messagingSenderId: '578841815881',
    projectId: 'trash2444',
    authDomain: 'trash2444.firebaseapp.com',
    databaseURL:
        'https://trash2444-default-rtdb.asia-southeast1.firebasedatabase.app',
    storageBucket: 'trash2444.firebasestorage.app',
    measurementId: 'G-VECV9HCK9M',
  );

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyBWpujFV1iH0Q7xCI8DEvuTTxj6PRTbuBk',
    appId: '1:578841815881:web:2de019e6535cd8b4738898',
    messagingSenderId: '578841815881',
    projectId: 'trash2444',
    authDomain: 'trash2444.firebaseapp.com',
    databaseURL:
        'https://trash2444-default-rtdb.asia-southeast1.firebasedatabase.app',
    storageBucket: 'trash2444.firebasestorage.app',
  );

  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'AIzaSyBWpujFV1iH0Q7xCI8DEvuTTxj6PRTbuBk',
    appId: '1:578841815881:web:2de019e6535cd8b4738898',
    messagingSenderId: '578841815881',
    projectId: 'trash2444',
    authDomain: 'trash2444.firebaseapp.com',
    databaseURL:
        'https://trash2444-default-rtdb.asia-southeast1.firebasedatabase.app',
    storageBucket: 'trash2444.firebasestorage.app',
    iosBundleId: 'com.example.noviFlutterApp',
  );

  static const FirebaseOptions macos = FirebaseOptions(
    apiKey: 'AIzaSyBWpujFV1iH0Q7xCI8DEvuTTxj6PRTbuBk',
    appId: '1:578841815881:web:2de019e6535cd8b4738898',
    messagingSenderId: '578841815881',
    projectId: 'trash2444',
    authDomain: 'trash2444.firebaseapp.com',
    databaseURL:
        'https://trash2444-default-rtdb.asia-southeast1.firebasedatabase.app',
    storageBucket: 'trash2444.firebasestorage.app',
    iosBundleId: 'com.example.noviFlutterApp',
  );

  static const FirebaseOptions windows = FirebaseOptions(
    apiKey: 'AIzaSyBWpujFV1iH0Q7xCI8DEvuTTxj6PRTbuBk',
    appId: '1:578841815881:web:2de019e6535cd8b4738898',
    messagingSenderId: '578841815881',
    projectId: 'trash2444',
    authDomain: 'trash2444.firebaseapp.com',
    databaseURL:
        'https://trash2444-default-rtdb.asia-southeast1.firebasedatabase.app',
    storageBucket: 'trash2444.firebasestorage.app',
    measurementId: 'G-VECV9HCK9M',
  );
}
