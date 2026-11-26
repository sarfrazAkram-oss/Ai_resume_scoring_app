import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';

class JobItem {
  const JobItem({
    this.id,
    required this.title,
    required this.department,
    required this.requiredSkills,
    required this.experience,
    required this.education,
    required this.description,
    required this.location,
    required this.employmentType,
    required this.salaryRange,
    required this.applicants,
    required this.status,
    this.jobType = 'fresh_graduate',
    this.skillsRequirement = 'required',
    this.experienceRequirement = 'preferred',
    this.experienceYears,
    this.educationRequirement = 'required',
    this.projectsRequirement = 'preferred',
    this.projectCriteria = '',
    this.scoringPolicyVersion = 2,
  });

  final String? id;
  final String title;
  final String department;
  final String requiredSkills;
  final String experience;
  final String education;
  final String description;
  final String location;
  final String employmentType;
  final String salaryRange;
  final int applicants;
  final String status;
  final String jobType;
  final String skillsRequirement;
  final String experienceRequirement;
  final String? experienceYears;
  final String educationRequirement;
  final String projectsRequirement;
  final String projectCriteria;
  final int? scoringPolicyVersion;

  factory JobItem.fromFirestore(
    DocumentSnapshot<Map<String, dynamic>> document,
  ) {
    final data = document.data() ?? <String, dynamic>{};
    final requirements = data['requirements'] as String? ?? '';
    final storedStatus = (data['status'] as String?)?.trim().toLowerCase();
    final policyVersion = data['scoringPolicyVersion'] as int?;
    return JobItem(
      id: document.id,
      title: data['title'] as String? ?? '',
      department: data['companyName'] as String? ?? '',
      requiredSkills: data['requiredSkills'] as String? ?? requirements,
      experience: data['requiredExperience'] as String? ?? '',
      education: data['requiredEducation'] as String? ?? '',
      description: data['description'] as String? ?? '',
      location: data['location'] as String? ?? '',
      employmentType: data['employmentType'] as String? ?? '',
      salaryRange: data['salary'] as String? ?? '',
      applicants: data['applicants'] as int? ?? 0,
      status:
          storedStatus == null ||
              storedStatus.isEmpty ||
              storedStatus == 'active' ||
              storedStatus == 'open'
          ? 'Open'
          : 'Closed',
      jobType: (data['jobType'] as String?) ?? 'fresh_graduate',
      skillsRequirement: (data['skillsRequirement'] as String?) ?? 'required',
      experienceRequirement:
          (data['experienceRequirement'] as String?) ?? 'preferred',
      experienceYears:
          data['experienceYears'] as String? ??
          (data['minimumExperienceYears'] as String?) ??
          '',
      educationRequirement:
          (data['educationRequirement'] as String?) ?? 'required',
      projectsRequirement:
          (data['projectsRequirement'] as String?) ?? 'preferred',
      projectCriteria: (data['projectCriteria'] as String?) ?? '',
      scoringPolicyVersion: policyVersion,
    );
  }

  Map<String, dynamic> toFirestore({required String createdBy}) => {
    'title': title,
    'companyName': department,
    'description': description,
    'requirements': [
      requiredSkills,
      experience,
      education,
    ].where((value) => value.trim().isNotEmpty).join('\n'),
    'requiredSkills': requiredSkills,
    'requiredExperience': experience,
    'requiredEducation': education,
    'location': location,
    'employmentType': employmentType,
    'salary': salaryRange,
    'createdBy': createdBy,
    'createdAt': FieldValue.serverTimestamp(),
    'status': status.toLowerCase() == 'open' ? 'active' : 'inactive',
    if (scoringPolicyVersion != null) ...{
      'scoringPolicyVersion': scoringPolicyVersion,
      'jobType': jobType,
      'skillsRequirement': skillsRequirement,
      'experienceRequirement': experienceRequirement,
      'experienceYears': experienceYears,
      'educationRequirement': educationRequirement,
      'projectsRequirement': projectsRequirement,
      'projectCriteria': projectCriteria,
    },
  };

  bool hasSameScoringPolicyAs(JobItem other) =>
      scoringPolicyVersion == other.scoringPolicyVersion &&
      jobType == other.jobType &&
      requiredSkills == other.requiredSkills &&
      experience == other.experience &&
      education == other.education &&
      skillsRequirement == other.skillsRequirement &&
      experienceRequirement == other.experienceRequirement &&
      experienceYears == other.experienceYears &&
      educationRequirement == other.educationRequirement &&
      projectsRequirement == other.projectsRequirement &&
      projectCriteria == other.projectCriteria;
}

class ResumeScoreBreakdown {
  const ResumeScoreBreakdown({
    this.skillsScore,
    this.experienceScore,
    this.educationScore,
    this.projectsScore,
    this.practicalWorkScore,
    required this.finalScore,
    this.skillsMax,
    this.experienceMax,
    this.educationMax,
    this.projectsMax,
    this.practicalWorkMax,
  });

  final double? skillsScore;
  final double? experienceScore;
  final double? educationScore;
  final double? projectsScore;
  final double? practicalWorkScore;
  final double finalScore;
  final int? skillsMax;
  final int? experienceMax;
  final int? educationMax;
  final int? projectsMax;
  final int? practicalWorkMax;

  factory ResumeScoreBreakdown.fromMap(Map<String, dynamic> data) {
    final finalScoreValue = _coerceDouble(data['finalScore']) ?? 0.0;
    return ResumeScoreBreakdown(
      skillsScore: _coerceDouble(data['skillsScore']),
      experienceScore: _coerceDouble(data['experienceScore']),
      educationScore: _coerceDouble(data['educationScore']),
      projectsScore: _coerceDouble(data['projectsScore']),
      practicalWorkScore: _coerceDouble(
        data['practicalWorkScore'] ?? data['projectsScore'],
      ),
      finalScore: finalScoreValue,
      skillsMax: data['skillsMax'] as int? ?? 40,
      experienceMax: data['experienceMax'] as int? ?? 25,
      educationMax: data['educationMax'] as int? ?? 20,
      projectsMax: data['projectsMax'] as int? ?? 15,
      practicalWorkMax:
          data['practicalWorkMax'] as int? ?? data['projectsMax'] as int? ?? 15,
    );
  }

  Map<String, dynamic> toMap() => {
    if (skillsScore != null) 'skillsScore': skillsScore,
    if (experienceScore != null) 'experienceScore': experienceScore,
    if (educationScore != null) 'educationScore': educationScore,
    if (projectsScore != null) 'projectsScore': projectsScore,
    if (practicalWorkScore != null) 'practicalWorkScore': practicalWorkScore,
    'finalScore': finalScore,
    if (skillsMax != null) 'skillsMax': skillsMax,
    if (experienceMax != null) 'experienceMax': experienceMax,
    if (educationMax != null) 'educationMax': educationMax,
    if (projectsMax != null) 'projectsMax': projectsMax,
    if (practicalWorkMax != null) 'practicalWorkMax': practicalWorkMax,
  };

  static double? _coerceDouble(Object? value) {
    if (value is num) {
      return value.toDouble();
    }
    if (value is String) {
      return double.tryParse(value);
    }
    return null;
  }
}

class ApplicationRecord {
  const ApplicationRecord({
    required this.id,
    this.candidateId = '',
    this.recruiterId = '',
    this.jobId = '',
    required this.candidateName,
    this.candidateEmail = '',
    required this.jobTitle,
    required this.resumeFileName,
    this.resumeStoragePath,
    required this.submittedAt,
    required this.status,
    this.resumeScore,
    this.breakdown,
    this.scoringStatus = 'pending',
    this.scoreShared = false,
    this.scoringModelVersion,
    this.scoringErrorCode,
    this.interviewDate,
    this.interviewTime,
    this.interviewPlatform,
    this.meetingLink,
  });

  final String id;
  final String candidateId;
  final String recruiterId;
  final String jobId;
  final String candidateName;
  final String candidateEmail;
  final String jobTitle;
  final String resumeFileName;
  final String? resumeStoragePath;
  final DateTime submittedAt;
  final String status;
  final double? resumeScore;
  final ResumeScoreBreakdown? breakdown;
  final String scoringStatus;
  final bool scoreShared;
  final int? scoringModelVersion;
  final String? scoringErrorCode;
  final String? interviewDate;
  final String? interviewTime;
  final String? interviewPlatform;
  final String? meetingLink;

  ApplicationRecord copyWith({
    String? status,
    String? scoringStatus,
    int? scoringModelVersion,
    String? scoringErrorCode,
    bool? scoreShared,
    double? resumeScore,
    ResumeScoreBreakdown? breakdown,
    String? interviewDate,
    String? interviewTime,
    String? interviewPlatform,
    String? meetingLink,
  }) {
    return ApplicationRecord(
      id: id,
      candidateId: candidateId,
      recruiterId: recruiterId,
      jobId: jobId,
      candidateName: candidateName,
      candidateEmail: candidateEmail,
      jobTitle: jobTitle,
      resumeFileName: resumeFileName,
      resumeStoragePath: resumeStoragePath,
      submittedAt: submittedAt,
      status: status ?? this.status,
      resumeScore: resumeScore ?? this.resumeScore,
      breakdown: breakdown ?? this.breakdown,
      scoringStatus: scoringStatus ?? this.scoringStatus,
      scoringModelVersion: scoringModelVersion ?? this.scoringModelVersion,
      scoringErrorCode: scoringErrorCode ?? this.scoringErrorCode,
      scoreShared: scoreShared ?? this.scoreShared,
      interviewDate: interviewDate ?? this.interviewDate,
      interviewTime: interviewTime ?? this.interviewTime,
      interviewPlatform: interviewPlatform ?? this.interviewPlatform,
      meetingLink: meetingLink ?? this.meetingLink,
    );
  }

  factory ApplicationRecord.fromFirestore(
    DocumentSnapshot<Map<String, dynamic>> document,
  ) {
    final data = document.data() ?? <String, dynamic>{};
    final appliedAt = data['appliedAt'];
    final scoreValue = data['score'];
    final scoreBreakdown = data['scoreBreakdown'];
    final modelVersion =
        data['scoringModelVersion'] ??
        (scoreBreakdown is Map<String, dynamic>
            ? scoreBreakdown['scoringModelVersion']
            : null);
    final scoringStatus = (data['scoringStatus'] as String?)?.trim();
    final storedStatus = data['status'] as String? ?? 'Pending';
    return ApplicationRecord(
      id: document.id,
      candidateId: data['candidateId'] as String? ?? '',
      recruiterId: data['recruiterId'] as String? ?? '',
      jobId: data['jobId'] as String? ?? '',
      candidateName: data['candidateName'] as String? ?? 'Candidate',
      candidateEmail: data['candidateEmail'] as String? ?? '',
      jobTitle: data['jobTitle'] as String? ?? data['jobId'] as String? ?? '',
      resumeFileName: data['resumeFileName'] as String? ?? '',
      resumeStoragePath: data['resumeStoragePath'] as String?,
      submittedAt: appliedAt is Timestamp ? appliedAt.toDate() : DateTime.now(),
      status: storedStatus,
      resumeScore: scoreValue is num ? scoreValue.toDouble() : null,
      breakdown: scoreBreakdown is Map<String, dynamic>
          ? ResumeScoreBreakdown.fromMap(scoreBreakdown)
          : null,
      scoringStatus:
          scoringStatus ?? (scoreValue == null ? 'pending' : 'scored'),
      scoreShared: data['scoreShared'] as bool? ?? false,
      scoringModelVersion: modelVersion is num ? modelVersion.toInt() : null,
      scoringErrorCode: data['scoringErrorCode'] as String?,
      interviewDate: data['interviewDate'] as String?,
      interviewTime: data['interviewTime'] as String?,
      interviewPlatform: data['interviewPlatform'] as String?,
      meetingLink: data['meetingLink'] as String?,
    );
  }
}

class CandidateNotification {
  const CandidateNotification({
    required this.id,
    required this.candidateId,
    required this.applicationId,
    required this.jobId,
    required this.type,
    required this.title,
    required this.message,
    required this.createdAt,
    required this.read,
  });

  final String id;
  final String candidateId;
  final String applicationId;
  final String jobId;
  final String type;
  final String title;
  final String message;
  final DateTime createdAt;
  final bool read;

  factory CandidateNotification.fromFirestore(
    DocumentSnapshot<Map<String, dynamic>> document,
  ) {
    final data = document.data();
    if (data == null) {
      throw StateError('Candidate notification data is missing.');
    }

    String requiredString(String field) {
      final value = data[field];
      if (value is! String || value.trim().isEmpty) {
        throw StateError('Candidate notification $field is missing.');
      }
      return value;
    }

    final createdAt = data['createdAt'];
    if (createdAt is! Timestamp) {
      throw StateError('Candidate notification createdAt is missing.');
    }
    final read = data['read'];
    if (read is! bool) {
      throw StateError('Candidate notification read state is missing.');
    }

    return CandidateNotification(
      id: document.id,
      candidateId: requiredString('candidateId'),
      applicationId: requiredString('applicationId'),
      jobId: requiredString('jobId'),
      type: requiredString('type'),
      title: requiredString('title'),
      message: requiredString('message'),
      createdAt: createdAt.toDate(),
      read: read,
    );
  }
}

class RecruiterLocalStore {
  RecruiterLocalStore._();

  static const String candidateName = 'Ahmed Khan';

  static final ValueNotifier<List<JobItem>> jobs = ValueNotifier(<JobItem>[]);

  static final ValueNotifier<int> jobCount = ValueNotifier<int>(
    jobs.value.length,
  );
  static final ValueNotifier<List<ApplicationRecord>> applications =
      ValueNotifier<List<ApplicationRecord>>(<ApplicationRecord>[]);

  static void addJob(JobItem job) {
    jobs.value = [job, ...jobs.value];
    jobCount.value = jobs.value.length;
  }

  static void updateJob(int index, JobItem job) {
    final updatedJobs = List<JobItem>.from(jobs.value);
    if (index < 0 || index >= updatedJobs.length) {
      return;
    }

    updatedJobs[index] = job;
    jobs.value = updatedJobs;
    jobCount.value = updatedJobs.length;
  }

  static void deleteJob(int index) {
    final updatedJobs = List<JobItem>.from(jobs.value);
    if (index < 0 || index >= updatedJobs.length) {
      return;
    }

    updatedJobs.removeAt(index);
    jobs.value = updatedJobs;
    jobCount.value = updatedJobs.length;
  }

  static void addApplication(ApplicationRecord application) {
    applications.value = [application, ...applications.value];
  }

  static void updateApplicationStatus(
    String applicationId,
    String status, {
    String? interviewDate,
    String? interviewTime,
    String? interviewPlatform,
    String? meetingLink,
  }) {
    final updatedApplications = applications.value.map((application) {
      if (application.id != applicationId) {
        return application;
      }

      return application.copyWith(
        status: status,
        interviewDate: interviewDate,
        interviewTime: interviewTime,
        interviewPlatform: interviewPlatform,
        meetingLink: meetingLink,
      );
    }).toList();

    applications.value = updatedApplications;
  }
}
