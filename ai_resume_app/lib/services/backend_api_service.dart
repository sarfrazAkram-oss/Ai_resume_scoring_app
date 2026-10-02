import 'dart:async';
import 'dart:convert';

import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class BackendApiService {
  BackendApiService({
    http.Client? client,
    String? baseUrl,
    Future<String?> Function()? idTokenProvider,
  }) : _client = client ?? http.Client(),
       _baseUrl = _normalizeBaseUrl(
         baseUrl ??
             resolveBaseUrl(
               isWeb: kIsWeb,
               platform: defaultTargetPlatform,
               configuredUrl: const String.fromEnvironment('BACKEND_URL'),
             ),
       ),
       _idTokenProvider = idTokenProvider ?? _currentFirebaseIdToken;

  static final BackendApiService instance = BackendApiService();

  final http.Client _client;
  final String _baseUrl;
  final Future<String?> Function() _idTokenProvider;

  static String resolveBaseUrl({
    required bool isWeb,
    required TargetPlatform platform,
    String configuredUrl = '',
  }) {
    final override = configuredUrl.trim();
    if (override.isNotEmpty) return _normalizeBaseUrl(override);
    if (isWeb || platform == TargetPlatform.windows) {
      return 'http://127.0.0.1:8000';
    }
    if (platform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://127.0.0.1:8000';
  }

  static String _normalizeBaseUrl(String value) =>
      value.trim().replaceFirst(RegExp(r'/+$'), '');

  static Future<String?> _currentFirebaseIdToken() async {
    final user = FirebaseAuth.instance.currentUser;
    return user?.getIdToken(true);
  }

  Future<void> scoreApplication({required String applicationId}) async {
    final idToken = await _idTokenProvider();
    if (idToken == null || idToken.trim().isEmpty) {
      throw const BackendScoringException();
    }

    final response = await _client
        .post(
          Uri.parse('$_baseUrl/score-application'),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $idToken',
          },
          body: jsonEncode({'applicationId': applicationId}),
        )
        .timeout(const Duration(seconds: 30));

    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw const BackendScoringException();
    }
  }
}

class BackendScoringException implements Exception {
  const BackendScoringException();

  @override
  String toString() => 'Resume scoring request failed.';
}
