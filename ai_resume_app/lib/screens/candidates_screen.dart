import 'package:flutter/material.dart';

import '../services/firestore_service.dart';
import 'job_management_screen.dart';
import 'local_resume_store.dart';

class CandidatesScreen extends StatelessWidget {
  const CandidatesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return RecruiterModuleShell(
      title: 'Candidates',
      subtitle: 'Ranked candidates for each job posting.',
      actionLabel: 'Back to Dashboard',
      actionIcon: Icons.arrow_back_rounded,
      actionOnPressed: () => Navigator.of(context).pop(),
      children: [
        const SizedBox(height: 24),
        StreamBuilder<List<ApplicationRecord>>(
          stream: FirestoreService.recruiterApplications(),
          builder: (context, snapshot) {
            if (snapshot.hasError) {
              return InfoCard(
                accentColor: const Color(0xFFDC2626),
                child: Text('Could not load candidates: ${snapshot.error}'),
              );
            }
            if (!snapshot.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final applications = snapshot.data!;
            if (applications.isEmpty) {
              return InfoCard(
                accentColor: const Color(0xFF167A5C),
                child: Text(
                  'No candidates available yet.',
                  style: InfoStyles.title,
                ),
              );
            }

            final rankedApplications =
                List<ApplicationRecord>.from(applications)..sort((left, right) {
                  final leftGroup = left.jobId.isNotEmpty
                      ? left.jobId
                      : left.jobTitle;
                  final rightGroup = right.jobId.isNotEmpty
                      ? right.jobId
                      : right.jobTitle;
                  final groupCompare = leftGroup.compareTo(rightGroup);
                  if (groupCompare != 0) {
                    return groupCompare;
                  }

                  final leftScored = left.scoringStatus == 'scored' ? 1 : 0;
                  final rightScored = right.scoringStatus == 'scored' ? 1 : 0;
                  if (leftScored != rightScored) {
                    return rightScored.compareTo(leftScored);
                  }

                  return (right.resumeScore ?? -1).compareTo(
                    left.resumeScore ?? -1,
                  );
                });
            final ranksByApplicationId = <String, int>{};
            var currentJobGroup = '';
            var nextRank = 0;
            for (final application in rankedApplications) {
              final jobGroup = application.jobId.isNotEmpty
                  ? application.jobId
                  : application.jobTitle;
              if (jobGroup != currentJobGroup) {
                currentJobGroup = jobGroup;
                nextRank = 0;
              }
              if (application.scoringStatus == 'scored' &&
                  application.resumeScore != null) {
                ranksByApplicationId[application.id] = ++nextRank;
              }
            }

            return Column(
              children: rankedApplications
                  .map(
                    (application) => Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: InfoCard(
                        accentColor: const Color(0xFF167A5C),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if (ranksByApplicationId[application.id]
                                case final rank?)
                              Text(
                                'Rank #$rank',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            Text(
                              application.candidateName,
                              style: InfoStyles.title,
                            ),
                            const SizedBox(height: 8),
                            Text('Applied Job: ${application.jobTitle}'),
                            Text('Resume Score: ${_scoreLabel(application)}'),
                            Text(
                              'Score sharing: ${application.scoreShared ? 'Shared' : 'Not Shared'}',
                            ),
                            if (application.breakdown != null) ...[
                              Text(
                                'Skills: ${application.breakdown!.skillsScore?.toStringAsFixed(0) ?? '0'} / ${application.breakdown!.skillsMax ?? 40}',
                              ),
                              Text(
                                'Experience: ${application.breakdown!.experienceScore?.toStringAsFixed(0) ?? '0'} / ${application.breakdown!.experienceMax ?? 25}',
                              ),
                              Text(
                                'Education: ${application.breakdown!.educationScore?.toStringAsFixed(0) ?? '0'} / ${application.breakdown!.educationMax ?? 20}',
                              ),
                              Text(
                                'Practical Work & Achievements: ${application.breakdown!.practicalWorkScore?.toStringAsFixed(0) ?? '0'} / ${application.breakdown!.practicalWorkMax ?? 15}',
                              ),
                            ],
                            Text('Current Status: ${application.status}'),
                          ],
                        ),
                      ),
                    ),
                  )
                  .toList(),
            );
          },
        ),
      ],
    );
  }

  String _scoreLabel(ApplicationRecord application) {
    if (application.scoringStatus == 'failed') {
      return 'Scoring failed';
    }
    if (application.resumeScore == null) {
      return 'Pending';
    }
    final value = application.resumeScore!;
    final formatted = value % 1 == 0
        ? value.toStringAsFixed(0)
        : value.toStringAsFixed(2);
    return '$formatted / 100';
  }
}
