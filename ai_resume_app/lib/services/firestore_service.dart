import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../screens/local_resume_store.dart';
import 'backend_api_service.dart';

class FirestoreService {
  FirestoreService._();

  static final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  static final FirebaseAuth _auth = FirebaseAuth.instance;

  static CollectionReference<Map<String, dynamic>> get _jobs =>
      _firestore.collection('jobs');

  static CollectionReference<Map<String, dynamic>> get _applications =>
      _firestore.collection('applications');

  static CollectionReference<Map<String, dynamic>> get _candidateApplications =>
      _firestore.collection('candidateApplications');

  static Stream<List<JobItem>> recruiterJobs() {
    final uid = _auth.currentUser?.uid;
    if (uid == null) {
      return Stream.value(const <JobItem>[]);
    }
    return _jobs
        .where('createdBy', isEqualTo: uid)
        .orderBy('createdAt', descending: true)
        .snapshots()
        .map((snapshot) => snapshot.docs.map(JobItem.fromFirestore).toList());
  }

  static Stream<List<JobItem>> activeJobs() {
    debugPrint('Available Jobs query started');
    debugPrint(
      'Available Jobs Firestore query: collection("jobs")'
      '.where("status", isEqualTo: "active")'
      '.orderBy("createdAt", descending: true)',
    );

    final query = _jobs
        .where('status', isEqualTo: 'active')
        .orderBy('createdAt', descending: true);
    return query
        .snapshots()
        .map((snapshot) {
          debugPrint(
            'Available Jobs query returned ${snapshot.docs.length} documents.',
          );
          return snapshot.docs.map(JobItem.fromFirestore).toList();
        })
        .handleError((Object error, StackTrace stackTrace) {
          debugPrint('Available Jobs query error: $error');
          Error.throwWithStackTrace(error, stackTrace);
        });
  }

  static Future<void> createJob(JobItem job) async {
    final user = _auth.currentUser;
    if (user == null) {
      throw StateError('You must be signed in to create a job.');
    }
    await _jobs.add(job.toFirestore(createdBy: user.uid));
  }

  static Future<void> updateJob(JobItem job) async {
    final id = job.id;
    if (id == null) throw StateError('The job document ID is missing.');
    final user = _auth.currentUser;
    if (user == null) throw StateError('You must be signed in to edit a job.');
    final jobReference = _jobs.doc(id);
    final existingSnapshot = await jobReference.get();
    if (!existingSnapshot.exists) {
      throw StateError('This job no longer exists.');
    }

    final applications = await _applications
        .where('recruiterId', isEqualTo: user.uid)
        .where('jobId', isEqualTo: id)
        .limit(1)
        .get();
    if (applications.docs.isNotEmpty) {
      final existingJob = JobItem.fromFirestore(existingSnapshot);
      if (!existingJob.hasSameScoringPolicyAs(job)) {
        throw StateError(
          'Scoring requirements cannot be changed after candidates have applied. '
          'Edit only non-scoring job details to preserve existing candidate scores.',
        );
      }
    }

    await jobReference.update(job.toFirestore(createdBy: user.uid));
  }

  static Future<void> deleteJob(JobItem job) async {
    final id = job.id;
    if (id == null) throw StateError('The job document ID is missing.');
    await _jobs.doc(id).delete();
  }

  static Stream<List<ApplicationRecord>> candidateApplications() {
    final uid = _auth.currentUser?.uid;
    if (uid == null) return Stream.value(const <ApplicationRecord>[]);
    return _candidateApplications
        .where('candidateId', isEqualTo: uid)
        .orderBy('appliedAt', descending: true)
        .snapshots()
        .map(
          (snapshot) =>
              snapshot.docs.map(ApplicationRecord.fromFirestore).toList(),
        );
  }

  static Stream<List<ApplicationRecord>> recruiterApplications() {
    final uid = _auth.currentUser?.uid;
    if (uid == null) return Stream.value(const <ApplicationRecord>[]);
    return _applications
        .where('recruiterId', isEqualTo: uid)
        .orderBy('appliedAt', descending: true)
        .snapshots()
        .map(
          (snapshot) =>
              snapshot.docs.map(ApplicationRecord.fromFirestore).toList(),
        );
  }

  static Future<String> createApplication({
    required JobItem job,
    required String resumeFileName,
    required Uint8List resumeBytes,
  }) async {
    final user = _auth.currentUser;
    if (user == null) throw StateError('You must be signed in to apply.');
    final jobId = job.id;
    if (jobId == null) throw StateError('The job document ID is missing.');

    debugPrint('STEP 1: Reading selected job document');
    late final DocumentSnapshot<Map<String, dynamic>> jobSnapshot;
    try {
      jobSnapshot = await _jobs.doc(jobId).get();
      debugPrint(
        'STEP 1 SUCCESS: Selected job read completed '
        '(exists: ${jobSnapshot.exists})',
      );
    } catch (error, stackTrace) {
      debugPrint('STEP 1 ERROR: Selected job read failed');
      Error.throwWithStackTrace(error, stackTrace);
    }
    final jobData = jobSnapshot.data();
    final recruiterId = jobData?['createdBy'] as String?;
    if (!jobSnapshot.exists || recruiterId == null || recruiterId.isEmpty) {
      throw StateError('The selected job owner could not be verified.');
    }

    debugPrint('STEP 2: Checking for an existing application');
    late final bool duplicate;
    try {
      duplicate = await BackendApiService.instance.hasApplicationForJob(
        jobId: jobId,
      );
      debugPrint(
        'STEP 2 SUCCESS: Duplicate application check completed '
        '(matches: ${duplicate ? 1 : 0})',
      );
    } catch (error, stackTrace) {
      debugPrint('STEP 2 ERROR: Duplicate application check failed');
      Error.throwWithStackTrace(error, stackTrace);
    }
    if (duplicate) {
      throw StateError('You have already applied to this job.');
    }

    final extension = resumeFileName.split('.').last.toLowerCase();
    if (extension != 'pdf' && extension != 'docx') {
      throw StateError('Only PDF and DOCX resumes are supported.');
    }
    final applicationReference = _applications.doc();
    final candidateName = user.displayName?.trim().isNotEmpty == true
        ? user.displayName!
        : user.email ?? 'Candidate';

    debugPrint('STEP 3: Uploading resume to Supabase Storage');
    late final String resumeStoragePath;
    try {
      resumeStoragePath = await BackendApiService.instance.uploadResume(
        applicationId: applicationReference.id,
        jobId: jobId,
        resumeFileName: resumeFileName,
        resumeBytes: resumeBytes,
      );
    } catch (error, stackTrace) {
      if (error is BackendApplicationException && error.statusCode != null) {
        debugPrint(
          'STEP 3 ERROR: type=${error.runtimeType} HTTP ${error.statusCode} '
          'detail=${BackendApiService.sanitizeDiagnosticDetail(error.detail)}',
        );
      } else {
        debugPrint(
          'STEP 3 ERROR: type=${error.runtimeType} '
          'category=${BackendApiService.diagnosticCategory(error)}',
        );
      }
      Error.throwWithStackTrace(
        StateError(
          'Resume upload failed. Please check your connection and try again.',
        ),
        stackTrace,
      );
    }

    debugPrint('STEP 4: Creating application document');
    try {
      await BackendApiService.instance.submitApplication(
        applicationId: applicationReference.id,
        jobId: jobId,
        resumeFileName: resumeFileName,
        resumeStoragePath: resumeStoragePath,
        candidateName: candidateName,
        candidateEmail: user.email ?? '',
      );
      debugPrint('STEP 4 SUCCESS: Application document created');
    } catch (error, stackTrace) {
      final exceptionType = error.runtimeType;
      if (error is BackendApplicationException && error.statusCode != null) {
        debugPrint(
          'STEP 4 ERROR: type=$exceptionType HTTP ${error.statusCode} '
          'detail=${BackendApiService.sanitizeDiagnosticDetail(error.detail)}',
        );
      } else {
        debugPrint(
          'STEP 4 ERROR: type=$exceptionType '
          'category=${BackendApiService.diagnosticCategory(error)}',
        );
      }
      if (error is BackendApplicationException &&
          error.statusCode != null &&
          error.statusCode! >= 400 &&
          error.statusCode! < 500) {
        try {
          await Supabase.instance.client.storage.from('resumes').remove([
            resumeStoragePath,
          ]);
        } catch (_) {
          debugPrint('Resume cleanup after application rejection failed');
        }
      }
      Error.throwWithStackTrace(error, stackTrace);
    }

    return applicationReference.id;
  }

  static Future<void> updateApplicationStatus(
    ApplicationRecord application,
    String status,
  ) async {
    final batch = _firestore.batch();
    batch.update(_applications.doc(application.id), {'status': status});
    batch.update(_candidateApplications.doc(application.id), {
      'status': status,
    });
    await batch.commit();
  }

  static Future<void> shortlistApplication(
    ApplicationRecord application,
  ) async {
    final user = _auth.currentUser;
    if (user == null) {
      throw StateError('You must be signed in to shortlist a candidate.');
    }
    if (application.recruiterId != user.uid) {
      throw StateError('You are not authorized to update this application.');
    }

    await updateApplicationStatus(application, 'Shortlisted');
  }

  static Future<void> rejectApplication(ApplicationRecord application) async {
    final user = _auth.currentUser;
    if (user == null || application.recruiterId != user.uid) {
      throw StateError('You are not authorized to update this application.');
    }

    final batch = _firestore.batch();
    batch.update(_applications.doc(application.id), {'status': 'Rejected'});
    batch.update(_candidateApplications.doc(application.id), {
      'status': 'Rejected',
      'scoreShared': true,
      if (application.resumeScore != null) 'score': application.resumeScore,
    });
    await batch.commit();
  }

  static Future<void> shareScore(ApplicationRecord application) async {
    final user = _auth.currentUser;
    if (user == null || application.recruiterId != user.uid) {
      throw StateError('You are not authorized to share this score.');
    }
    final score = application.resumeScore;
    if (score == null) {
      throw StateError('A final score is not available yet.');
    }
    final breakdown = application.breakdown;
    if (breakdown == null) {
      throw StateError('A complete score breakdown is not available yet.');
    }
    final batch = _firestore.batch();
    batch.update(_applications.doc(application.id), {'scoreShared': true});
    batch.update(_candidateApplications.doc(application.id), {
      'score': score,
      'scoreBreakdown': breakdown.toMap(),
      'scoreShared': true,
    });
    await batch.commit();
  }
}
