import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/foundation.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../screens/local_resume_store.dart';

class FirestoreService {
  FirestoreService._();

  static final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  static final FirebaseAuth _auth = FirebaseAuth.instance;

  static CollectionReference<Map<String, dynamic>> get _jobs =>
      _firestore.collection('jobs');

  static CollectionReference<Map<String, dynamic>> get _applications =>
      _firestore.collection('applications');

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
    final user = _auth.currentUser;
    debugPrint('Available Jobs auth uid: ${user?.uid}');
    debugPrint('Available Jobs auth email: ${user?.email}');
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
    await _jobs.doc(id).update(job.toFirestore(createdBy: user.uid));
  }

  static Future<void> deleteJob(JobItem job) async {
    final id = job.id;
    if (id == null) throw StateError('The job document ID is missing.');
    await _jobs.doc(id).delete();
  }

  static Stream<List<ApplicationRecord>> candidateApplications() {
    final uid = _auth.currentUser?.uid;
    if (uid == null) return Stream.value(const <ApplicationRecord>[]);
    return _applications
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

    debugPrint('Application submit auth uid: ${user.uid}');
    debugPrint('Application submit auth email: ${user.email}');
    debugPrint('Application submit jobId: $jobId');

    debugPrint('STEP 1: Reading selected job document: jobs/$jobId');
    late final DocumentSnapshot<Map<String, dynamic>> jobSnapshot;
    try {
      jobSnapshot = await _jobs.doc(jobId).get();
      debugPrint(
        'STEP 1 SUCCESS: Selected job read completed '
        '(exists: ${jobSnapshot.exists})',
      );
    } catch (error, stackTrace) {
      debugPrint('STEP 1 ERROR: Selected job read failed: $error');
      Error.throwWithStackTrace(error, stackTrace);
    }
    final jobData = jobSnapshot.data();
    final recruiterId = jobData?['createdBy'] as String?;
    debugPrint('Application submit recruiterId: $recruiterId');
    if (!jobSnapshot.exists || recruiterId == null || recruiterId.isEmpty) {
      throw StateError('The selected job owner could not be verified.');
    }

    debugPrint(
      'STEP 2: Checking duplicate application '
      '(applications where jobId == $jobId and candidateId == ${user.uid})',
    );
    late final QuerySnapshot<Map<String, dynamic>> duplicate;
    try {
      duplicate = await _applications
          .where('jobId', isEqualTo: jobId)
          .where('candidateId', isEqualTo: user.uid)
          .limit(1)
          .get();
      debugPrint(
        'STEP 2 SUCCESS: Duplicate application check completed '
        '(matches: ${duplicate.docs.length})',
      );
    } catch (error, stackTrace) {
      debugPrint('STEP 2 ERROR: Duplicate application check failed: $error');
      Error.throwWithStackTrace(error, stackTrace);
    }
    if (duplicate.docs.isNotEmpty) {
      throw StateError('You have already applied to this job.');
    }

    final extension = resumeFileName.split('.').last.toLowerCase();
    final contentType = switch (extension) {
      'pdf' => 'application/pdf',
      'doc' => 'application/msword',
      'docx' =>
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      _ => throw StateError('Only PDF, DOC, and DOCX resumes are supported.'),
    };
    final applicationReference = _applications.doc();
    final resumeStoragePath =
        '${user.uid}/$jobId/${applicationReference.id}.$extension';

    debugPrint('STEP 3: Uploading resume to Supabase Storage');
    await Supabase.instance.client.storage
        .from('resumes')
        .uploadBinary(
          resumeStoragePath,
          resumeBytes,
          fileOptions: FileOptions(contentType: contentType, upsert: false),
        );

    debugPrint('STEP 4: Creating application document');
    try {
      await applicationReference.set({
        'jobId': jobId,
        'jobTitle': job.title,
        'companyName': job.department,
        'recruiterId': recruiterId,
        'candidateId': user.uid,
        'candidateEmail': user.email ?? '',
        'candidateName': user.displayName?.trim().isNotEmpty == true
            ? user.displayName
            : user.email ?? 'Candidate',
        'resumeFileName': resumeFileName,
        'resumeStoragePath': resumeStoragePath,
        'appliedAt': FieldValue.serverTimestamp(),
        'status': 'Pending',
        'score': null,
        'scoringStatus': 'pending',
      });
      debugPrint(
        'STEP 4 SUCCESS: Application document created '
        '(id: ${applicationReference.id})',
      );
    } catch (error, stackTrace) {
      debugPrint('STEP 4 ERROR: Application create failed: $error');
      try {
        await Supabase.instance.client.storage.from('resumes').remove([
          resumeStoragePath,
        ]);
      } catch (cleanupError) {
        debugPrint(
          'Resume cleanup after Firestore failure failed: $cleanupError',
        );
      }
      Error.throwWithStackTrace(error, stackTrace);
    }

    return applicationReference.id;
  }

  static Future<void> updateApplicationStatus(
    ApplicationRecord application,
    String status,
  ) async {
    await _applications.doc(application.id).update({'status': status});
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

    await _applications.doc(application.id).update({'status': 'Shortlisted'});
  }
}
