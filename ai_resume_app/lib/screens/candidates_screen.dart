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
                List<ApplicationRecord>.from(applications)..sort(
                  (left, right) => (right.resumeScore ?? -1).compareTo(
                    left.resumeScore ?? -1,
                  ),
                );

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
                            Text(
                              application.candidateName,
                              style: InfoStyles.title,
                            ),
                            const SizedBox(height: 8),
                            Text('Applied Job: ${application.jobTitle}'),
                            Text(
                              'Resume Score: ${application.resumeScore ?? 'Pending'}',
                            ),
                            if (application.breakdown != null) ...[
                              Text(
                                'Skills Match: ${application.breakdown!.skillsScore}%',
                              ),
                              Text(
                                'Experience Match: ${application.breakdown!.experienceScore}%',
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
}
