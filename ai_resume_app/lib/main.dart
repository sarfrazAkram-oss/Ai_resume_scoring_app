import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'firebase_options.dart';
import 'screens/splash_screen.dart';

const _supabaseUrl = String.fromEnvironment('SUPABASE_URL');
const _supabasePublishableKey = String.fromEnvironment(
  'SUPABASE_PUBLISHABLE_KEY',
);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  if (_supabaseUrl.isEmpty || _supabasePublishableKey.isEmpty) {
    throw StateError(
      'Provide SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY using --dart-define.',
    );
  }
  await Supabase.initialize(
    url: _supabaseUrl,
    publishableKey: _supabasePublishableKey,
    accessToken: () async => FirebaseAuth.instance.currentUser?.getIdToken(),
  );
  runApp(const AiResumeApp());
}

class AiResumeApp extends StatelessWidget {
  const AiResumeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'AI Resume System',
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF5F8FF),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF3D79D0),
          brightness: Brightness.light,
        ),
        textTheme: const TextTheme(
          bodyMedium: TextStyle(color: Color(0xFF41536B)),
          bodyLarge: TextStyle(color: Color(0xFF41536B)),
        ),
      ),
      home: const SplashScreen(),
    );
  }
}
