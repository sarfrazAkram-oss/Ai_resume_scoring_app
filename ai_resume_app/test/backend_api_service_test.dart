import 'dart:convert';

import 'package:ai_resume_app/services/backend_api_service.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  test('selects local backend URL by platform', () {
    expect(
      BackendApiService.resolveBaseUrl(
        isWeb: true,
        platform: TargetPlatform.android,
      ),
      'http://127.0.0.1:8000',
    );
    expect(
      BackendApiService.resolveBaseUrl(
        isWeb: false,
        platform: TargetPlatform.windows,
      ),
      'http://127.0.0.1:8000',
    );
    expect(
      BackendApiService.resolveBaseUrl(
        isWeb: false,
        platform: TargetPlatform.android,
      ),
      'http://10.0.2.2:8000',
    );
    expect(
      BackendApiService.resolveBaseUrl(
        isWeb: false,
        platform: TargetPlatform.android,
        configuredUrl: 'http://192.168.1.4:8000/',
      ),
      'http://192.168.1.4:8000',
    );
  });

  test('sends only the application ID with a fresh Firebase token', () async {
    var tokenRequests = 0;
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.toString(), 'http://127.0.0.1:8000/score-application');
      expect(request.headers['content-type'], 'application/json');
      expect(request.headers['authorization'], 'Bearer fresh-id-token');
      expect(jsonDecode(request.body), {'applicationId': 'application-123'});
      return http.Response('{}', 200);
    });
    final service = BackendApiService(
      client: client,
      baseUrl: 'http://127.0.0.1:8000/',
      idTokenProvider: () async {
        tokenRequests++;
        return 'fresh-id-token';
      },
    );

    await service.scoreApplication(applicationId: 'application-123');

    expect(tokenRequests, 1);
  });

  test('does not include backend response details in scoring errors', () async {
    final service = BackendApiService(
      client: MockClient(
        (_) async => http.Response('internal stack trace', 500),
      ),
      baseUrl: 'http://127.0.0.1:8000',
      idTokenProvider: () async => 'fresh-id-token',
    );

    await expectLater(
      service.scoreApplication(applicationId: 'application-123'),
      throwsA(isA<BackendScoringException>()),
    );
  });
}
