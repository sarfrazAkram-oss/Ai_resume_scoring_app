import 'package:flutter/material.dart';

import 'screens/splash_screen.dart';

void main() {
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
