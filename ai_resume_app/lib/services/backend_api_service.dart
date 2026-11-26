import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

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

  static String sanitizeDiagnosticDetail(String? detail) {
    const safeDetails = {
      'An application already exists for this job or request.',
      'Authorization must be Bearer <token>',
      'Firebase authentication is not configured',
      'Invalid application request',
      'Invalid Firebase token',
      'Job not found',
      'Job ownership could not be verified',
      'Missing Authorization header',
      'Resume file exceeds the 10 MiB limit',
      'Resume file is empty',
      'Resume upload failed',
      'Unsupported resume file type',
      'Invalid resume file content',
      'You have already applied to this job.',
    };
    return detail != null && safeDetails.contains(detail) ? detail : 'redacted';
  }

  static String diagnosticCategory(Object error) {
    final type = error.runtimeType.toString();
    if (error is TimeoutException) return 'network-timeout';
    if (error is http.ClientException ||
        const {
          'HandshakeException',
          'HttpException',
          'SocketException',
        }.contains(type)) {
      return 'network-transport';
    }
    return 'application';
  }

  static Future<String?> _currentFirebaseIdToken() async {
    final user = FirebaseAuth.instance.currentUser;
    return user?.getIdToken(true);
  }

  Future<String> uploadResume({
    required String applicationId,
    required String jobId,
    required String resumeFileName,
    required Uint8List resumeBytes,
  }) async {
    final String? idToken;
    try {
      idToken = await _idTokenProvider();
    } on FirebaseAuthException catch (error) {
      throw BackendApplicationException(
        detail: 'Firebase authentication failed (${error.code}).',
      );
    }
    if (idToken == null || idToken.trim().isEmpty) {
      throw const BackendApplicationException(
        detail: 'A Firebase sign-in session is required.',
      );
    }

    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$_baseUrl/upload-resume'),
    )
      ..headers['Authorization'] = 'Bearer $idToken'
      ..fields['applicationId'] = applicationId
      ..fields['jobId'] = jobId
      ..files.add(
        http.MultipartFile.fromBytes(
          'file',
          resumeBytes,
          filename: resumeFileName,
        ),
      );

    final streamedResponse = await _client
        .send(request)
        .timeout(const Duration(seconds: 30));
    final response = await http.Response.fromStream(
      streamedResponse,
    ).timeout(const Duration(seconds: 30));

    Map<String, dynamic>? responseData;
    try {
      final decoded = jsonDecode(response.body);
      responseData = decoded is Map<String, dynamic> ? decoded : null;
    } on FormatException {
      responseData = null;
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final rawDetail = responseData?['detail'];
      final safeDetail =
          rawDetail is String &&
              rawDetail.length <= 240 &&
              !rawDetail.contains('Traceback')
          ? rawDetail.replaceAll(RegExp(r'[\r\n]+'), ' ')
          : 'The application API returned HTTP ${response.statusCode}.';
      throw BackendApplicationException(
        statusCode: response.statusCode,
        detail: safeDetail,
      );
    }

    final resumeStoragePath = responseData?['resumeStoragePath'];
    if (resumeStoragePath is! String || resumeStoragePath.isEmpty) {
      throw const BackendApplicationException(
        detail: 'The application API returned an invalid response.',
      );
    }
    return resumeStoragePath;
  }

  Future<bool> hasApplicationForJob({required String jobId}) async {
    final response = await _postApplicationRequest(
      '/application-duplicate-check',
      {'jobId': jobId},
    );
    final duplicate = response['duplicate'];
    if (duplicate is! bool) {
      throw const BackendApplicationException(
        detail: 'The application API returned an invalid response.',
      );
    }
    return duplicate;
  }

  Future<void> submitApplication({
    required String applicationId,
    required String jobId,
    required String resumeFileName,
    required String resumeStoragePath,
    required String candidateName,
    required String candidateEmail,
  }) async {
    await _postApplicationRequest('/submit-application', {
      'applicationId': applicationId,
      'jobId': jobId,
      'resumeFileName': resumeFileName,
      'resumeStoragePath': resumeStoragePath,
      'candidateName': candidateName,
      'candidateEmail': candidateEmail,
    });
  }

  Future<Map<String, dynamic>> _postApplicationRequest(
    String path,
    Map<String, String> payload,
  ) async {
    final String? idToken;
    try {
      idToken = await _idTokenProvider();
    } on FirebaseAuthException catch (error) {
      throw BackendApplicationException(
        detail: 'Firebase authentication failed (${error.code}).',
      );
    }
    if (idToken == null || idToken.trim().isEmpty) {
      throw const BackendApplicationException(
        detail: 'A Firebase sign-in session is required.',
      );
    }

    final response = await _client
        .post(
          Uri.parse('$_baseUrl$path'),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $idToken',
          },
          body: jsonEncode(payload),
        )
        .timeout(const Duration(seconds: 30));

    Map<String, dynamic>? responseData;
    try {
      final decoded = jsonDecode(response.body);
      responseData = decoded is Map<String, dynamic> ? decoded : null;
    } on FormatException {
      responseData = null;
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final rawDetail = responseData?['detail'];
      final safeDetail =
          rawDetail is String &&
              rawDetail.length <= 240 &&
              !rawDetail.contains('Traceback')
          ? rawDetail.replaceAll(RegExp(r'[\r\n]+'), ' ')
          : 'The application API returned HTTP ${response.statusCode}.';
      throw BackendApplicationException(
        statusCode: response.statusCode,
        detail: safeDetail,
      );
    }
    if (responseData == null) {
      throw const BackendApplicationException(
        detail: 'The application API returned an invalid response.',
      );
    }
    return responseData;
  }

  Future<ScoreApplicationResult> scoreApplication({
    required String applicationId,
    bool confirmRescore = false,
  }) async {
    final String? idToken;
    try {
      idToken = await _idTokenProvider();
    } on FirebaseAuthException catch (error) {
      throw BackendScoringException(
        detail: 'Firebase authentication failed (${error.code}).',
      );
    }
    if (idToken == null || idToken.trim().isEmpty) {
      throw const BackendScoringException(
        detail: 'A Firebase sign-in session is required.',
      );
    }

    final response = await _client
        .post(
          Uri.parse('$_baseUrl/score-application'),
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer $idToken',
          },
          body: jsonEncode({
            'applicationId': applicationId,
            if (confirmRescore) 'confirmRescore': true,
          }),
        )
        .timeout(const Duration(seconds: 30));

    Map<String, dynamic>? responseData;
    try {
      final decoded = jsonDecode(response.body);
      responseData = decoded is Map<String, dynamic> ? decoded : null;
    } on FormatException {
      responseData = null;
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final rawDetail = responseData?['detail'];
      final safeDetail =
          rawDetail is String &&
              rawDetail.length <= 240 &&
              !rawDetail.contains('Traceback')
          ? rawDetail.replaceAll(RegExp(r'[\r\n]+'), ' ')
          : 'The scoring API returned HTTP ${response.statusCode}.';
      throw BackendScoringException(
        statusCode: response.statusCode,
        detail: safeDetail,
      );
    }
    if (responseData == null) {
      throw BackendScoringException(
        statusCode: response.statusCode,
        detail: 'The scoring API returned an invalid response.',
      );
    }
    final score = responseData['score'];
    final scoringStatus = responseData['scoringStatus'];
    final modelVersion = responseData['scoringModelVersion'];
    if (score is! num || scoringStatus != 'scored') {
      throw BackendScoringException(
        statusCode: response.statusCode,
        detail: 'The scoring API did not return a completed score.',
      );
    }
    return ScoreApplicationResult(
      statusCode: response.statusCode,
      score: score.toDouble(),
      scoringStatus: scoringStatus as String,
      scoringModelVersion: modelVersion is num ? modelVersion.toInt() : null,
    );
  }
}

class ScoreApplicationResult {
  const ScoreApplicationResult({
    required this.statusCode,
    required this.score,
    required this.scoringStatus,
    this.scoringModelVersion,
  });

  final int statusCode;
  final double score;
  final String scoringStatus;
  final int? scoringModelVersion;
}

class BackendScoringException implements Exception {
  const BackendScoringException({this.statusCode, this.detail});

  final int? statusCode;
  final String? detail;

  @override
  String toString() => 'Resume scoring request failed.';
}

class BackendApplicationException implements Exception {
  const BackendApplicationException({this.statusCode, this.detail});

  final int? statusCode;
  final String? detail;

  @override
  String toString() => detail ?? 'Application submission failed.';
}
