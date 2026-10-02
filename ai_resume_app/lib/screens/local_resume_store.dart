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

  factory JobItem.fromFirestore(
    DocumentSnapshot<Map<String, dynamic>> document,
  ) {
    final data = document.data() ?? <String, dynamic>{};
    final requirements = data['requirements'] as String? ?? '';
    final storedStatus = (data['status'] as String?)?.trim().toLowerCase();
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
  };
}

class ResumeScoreBreakdown {
  const ResumeScoreBreakdown({
    this.skillsScore,
    this.experienceScore,
    this.educationScore,
    this.projectsScore,
    required this.finalScore,
    this.skillsMax,
    this.experienceMax,
    this.educationMax,
    this.projectsMax,
  });

  final double? skillsScore;
  final double? experienceScore;
  final double? educationScore;
  final double? projectsScore;
  final double finalScore;
  final int? skillsMax;
  final int? experienceMax;
  final int? educationMax;
  final int? projectsMax;

  factory ResumeScoreBreakdown.fromMap(Map<String, dynamic> data) {
    final finalScoreValue = _coerceDouble(data['finalScore']) ?? 0.0;
    return ResumeScoreBreakdown(
      skillsScore: _coerceDouble(data['skillsScore']),
      experienceScore: _coerceDouble(data['experienceScore']),
      educationScore: _coerceDouble(data['educationScore']),
      projectsScore: _coerceDouble(data['projectsScore']),
      finalScore: finalScoreValue,
      skillsMax: data['skillsMax'] as int? ?? 40,
      experienceMax: data['experienceMax'] as int? ?? 25,
      educationMax: data['educationMax'] as int? ?? 20,
      projectsMax: data['projectsMax'] as int? ?? 15,
    );
  }

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
  final String? scoringErrorCode;
  final String? interviewDate;
  final String? interviewTime;
  final String? interviewPlatform;
  final String? meetingLink;

  ApplicationRecord copyWith({
    String? status,
    String? scoringStatus,
    String? scoringErrorCode,
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
      scoringErrorCode: scoringErrorCode ?? this.scoringErrorCode,
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
      scoringErrorCode: data['scoringErrorCode'] as String?,
      interviewDate: data['interviewDate'] as String?,
      interviewTime: data['interviewTime'] as String?,
      interviewPlatform: data['interviewPlatform'] as String?,
      meetingLink: data['meetingLink'] as String?,
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
