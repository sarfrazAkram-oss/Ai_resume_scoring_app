import 'package:flutter/material.dart';

import '../services/firestore_service.dart';
import 'job_management_screen.dart';
import 'local_resume_store.dart';

class ApplicationsScreen extends StatelessWidget {
  const ApplicationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return RecruiterModuleShell(
      title: 'Applications',
      subtitle: 'Review submitted applications and take action.',
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
                child: Text('Could not load applications: ${snapshot.error}'),
              );
            }
            if (!snapshot.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final applications = snapshot.data!;
            if (applications.isEmpty) {
              return InfoCard(
                accentColor: const Color(0xFF7C3AED),
                child: Text(
                  'No applications available yet.',
                  style: InfoStyles.title,
                ),
              );
            }

            return Column(
              children: applications
                  .map(
                    (application) => Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: InfoCard(
                        accentColor: const Color(0xFF7C3AED),
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
                              'Candidate Email: ${application.candidateEmail}',
                            ),
                            Text('Resume: ${application.resumeFileName}'),
                            Text(
                              'Resume Score: ${application.resumeScore ?? 'Pending'}',
                            ),
                            Text(
                              'Applied Date: ${_formatDate(application.submittedAt)}',
                            ),
                            Text('Status: ${application.status}'),
                            const SizedBox(height: 12),
                            Wrap(
                              spacing: 10,
                              runSpacing: 10,
                              children: [
                                PillAction(
                                  label: 'Shortlist',
                                  onTap: () =>
                                      FirestoreService.updateApplicationStatus(
                                        application,
                                        'Shortlisted',
                                      ),
                                ),
                                PillAction(
                                  label: 'Interview Scheduled',
                                  onTap: () =>
                                      FirestoreService.updateApplicationStatus(
                                        application,
                                        'Interview Scheduled',
                                      ),
                                ),
                              ],
                            ),
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

  String _formatDate(DateTime dateTime) {
    const months = [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December',
    ];

    final day = dateTime.day.toString().padLeft(2, '0');
    return '$day ${months[dateTime.month - 1]} ${dateTime.year}';
  }
}
