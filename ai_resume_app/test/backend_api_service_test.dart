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

  test(
    'checks for duplicate applications with Firebase authentication',
    () async {
      final service = BackendApiService(
        client: MockClient((request) async {
          expect(request.method, 'POST');
          expect(
            request.url.toString(),
            'http://127.0.0.1:8000/application-duplicate-check',
          );
          expect(request.headers['authorization'], 'Bearer fresh-id-token');
          expect(jsonDecode(request.body), {'jobId': 'job-1'});
          return http.Response(jsonEncode({'duplicate': false}), 200);
        }),
        baseUrl: 'http://127.0.0.1:8000',
        idTokenProvider: () async => 'fresh-id-token',
      );

      expect(await service.hasApplicationForJob(jobId: 'job-1'), isFalse);
    },
  );

  test(
    'submits an application without trusting a client-supplied UID',
    () async {
      final service = BackendApiService(
        client: MockClient((request) async {
          expect(request.method, 'POST');
          expect(
            request.url.toString(),
            'http://127.0.0.1:8000/submit-application',
          );
          expect(request.headers['authorization'], 'Bearer fresh-id-token');
          expect(jsonDecode(request.body), {
            'applicationId': 'application-1',
            'jobId': 'job-1',
            'resumeFileName': 'resume.pdf',
            'resumeStoragePath': 'candidate-1/job-1/application-1.pdf',
            'candidateName': 'Candidate',
            'candidateEmail': 'candidate@example.com',
          });
          return http.Response(
            jsonEncode({'applicationId': 'application-1'}),
            200,
          );
        }),
        baseUrl: 'http://127.0.0.1:8000',
        idTokenProvider: () async => 'fresh-id-token',
      );

      await service.submitApplication(
        applicationId: 'application-1',
        jobId: 'job-1',
        resumeFileName: 'resume.pdf',
        resumeStoragePath: 'candidate-1/job-1/application-1.pdf',
        candidateName: 'Candidate',
        candidateEmail: 'candidate@example.com',
      );
    },
  );

  test('sends only the application ID with a fresh Firebase token', () async {
    var tokenRequests = 0;
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.toString(), 'http://127.0.0.1:8000/score-application');
      expect(request.headers['content-type'], 'application/json');
      expect(request.headers['authorization'], 'Bearer fresh-id-token');
      expect(jsonDecode(request.body), {'applicationId': 'application-123'});
      return http.Response(
        jsonEncode({
          'applicationId': 'application-123',
          'score': 79.0,
          'scoringStatus': 'scored',
          'scoringModelVersion': 3,
        }),
        200,
      );
    });
    final service = BackendApiService(
      client: client,
      baseUrl: 'http://127.0.0.1:8000/',
      idTokenProvider: () async {
        tokenRequests++;
        return 'fresh-id-token';
      },
    );

    final result = await service.scoreApplication(
      applicationId: 'application-123',
    );

    expect(tokenRequests, 1);
    expect(result.statusCode, 200);
    expect(result.score, 79);
    expect(result.scoringStatus, 'scored');
    expect(result.scoringModelVersion, 3);
  });

  test(
    'sends explicit confirmation when rescoring an existing application',
    () async {
      final service = BackendApiService(
        client: MockClient((request) async {
          expect(jsonDecode(request.body), {
            'applicationId': 'application-123',
            'confirmRescore': true,
          });
          return http.Response(
            jsonEncode({
              'applicationId': 'application-123',
              'score': 79.0,
              'scoringStatus': 'scored',
              'scoringModelVersion': 3,
            }),
            200,
          );
        }),
        baseUrl: 'http://127.0.0.1:8000',
        idTokenProvider: () async => 'fresh-id-token',
      );

      final result = await service.scoreApplication(
        applicationId: 'application-123',
        confirmRescore: true,
      );

      expect(result.statusCode, 200);
      expect(result.score, 79);
    },
  );

  test('reports safe HTTP status and backend error detail', () async {
    final service = BackendApiService(
      client: MockClient(
        (_) async => http.Response(
          jsonEncode({'detail': 'Application ownership mismatch'}),
          403,
        ),
      ),
      baseUrl: 'http://127.0.0.1:8000',
      idTokenProvider: () async => 'fresh-id-token',
    );

    await expectLater(
      service.scoreApplication(applicationId: 'application-123'),
      throwsA(
        isA<BackendScoringException>()
            .having((error) => error.statusCode, 'statusCode', 403)
            .having(
              (error) => error.detail,
              'detail',
              'Application ownership mismatch',
            ),
      ),
    );
  });

  test(
    'does not expose stack traces returned as a server error body',
    () async {
      final service = BackendApiService(
        client: MockClient(
          (_) async => http.Response('internal stack trace', 500),
        ),
        baseUrl: 'http://127.0.0.1:8000',
        idTokenProvider: () async => 'fresh-id-token',
      );

      await expectLater(
        service.scoreApplication(applicationId: 'application-123'),
        throwsA(
          isA<BackendScoringException>()
              .having((error) => error.statusCode, 'statusCode', 500)
              .having(
                (error) => error.detail,
                'detail',
                'The scoring API returned HTTP 500.',
              ),
        ),
      );
    },
  );
}
