import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:url_launcher/url_launcher.dart';

import '../services/firestore_service.dart';
import 'job_management_screen.dart';
import 'local_resume_store.dart';

class ApplicationsScreen extends StatefulWidget {
  const ApplicationsScreen({super.key});

  @override
  State<ApplicationsScreen> createState() => _ApplicationsScreenState();
}

class _ApplicationsScreenState extends State<ApplicationsScreen> {
  final Set<String> _loadingApplicationIds = <String>{};

  Future<void> _viewResume(ApplicationRecord application) async {
    final resumeStoragePath = application.resumeStoragePath;
    if (resumeStoragePath == null || resumeStoragePath.isEmpty) {
      _showMessage('Resume file path is missing for this application.');
      return;
    }

    setState(() => _loadingApplicationIds.add(application.id));
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) {
        _showMessage('Please sign in again to view this resume.');
        return;
      }
      final idToken = await user.getIdToken(true);
      if (idToken == null || idToken.isEmpty) {
        _showMessage('Could not authenticate the resume request.');
        return;
      }

      final response = await Supabase.instance.client.functions.invoke(
        'get-resume-url',
        body: {'applicationId': application.id},
        headers: {'Authorization': 'Bearer $idToken'},
      );
      final responseData = response.data;
      if (responseData is! Map || responseData['signedUrl'] is! String) {
        _showMessage('The server did not return a valid resume link.');
        return;
      }

      final signedUrl = Uri.tryParse(responseData['signedUrl'] as String);
      if (signedUrl == null ||
          signedUrl.scheme != 'https' ||
          signedUrl.host.isEmpty) {
        _showMessage('The server returned an invalid resume link.');
        return;
      }
      if (!await launchUrl(signedUrl, mode: LaunchMode.externalApplication)) {
        _showMessage('Could not open the resume link.');
      }
    } on FunctionsHttpException catch (error) {
      final message = switch (error.status) {
        401 => 'Your sign-in has expired. Please sign in again.',
        403 => 'You are not authorized to view this resume.',
        404 => 'The resume or application could not be found.',
        _ => 'The resume request failed. Please try again.',
      };
      _showMessage(message);
    } on FunctionException catch (error) {
      _showMessage(
        error.status == 0
            ? 'Could not connect to the resume service.'
            : 'The resume request failed. Please try again.',
      );
    } catch (_) {
      _showMessage('Could not open the resume. Please try again.');
    } finally {
      if (mounted) {
        setState(() => _loadingApplicationIds.remove(application.id));
      }
    }
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _shortlistApplication(ApplicationRecord application) async {
    try {
      await FirestoreService.shortlistApplication(application);
      _showMessage('Candidate shortlisted successfully.');
    } catch (_) {
      _showMessage('Could not shortlist candidate. Please try again.');
    }
  }

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
                                OutlinedButton.icon(
                                  onPressed:
                                      _loadingApplicationIds.contains(
                                        application.id,
                                      )
                                      ? null
                                      : () => _viewResume(application),
                                  icon:
                                      _loadingApplicationIds.contains(
                                        application.id,
                                      )
                                      ? const SizedBox(
                                          width: 18,
                                          height: 18,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                          ),
                                        )
                                      : const Icon(Icons.visibility_outlined),
                                  label: const Text('View Resume'),
                                ),
                                PillAction(
                                  label: 'Shortlist',
                                  onTap: () =>
                                      _shortlistApplication(application),
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
