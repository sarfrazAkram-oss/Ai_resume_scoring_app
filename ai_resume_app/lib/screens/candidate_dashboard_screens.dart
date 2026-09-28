import 'dart:async';

import 'package:file_picker/file_picker.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../services/firestore_service.dart';
import 'local_resume_store.dart';

class AvailableJobsScreen extends StatelessWidget {
  const AvailableJobsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Available Jobs'),
      ),
      body: StreamBuilder<List<JobItem>>(
        stream: FirestoreService.activeJobs(),
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(
              child: Text('Could not load jobs: ${snapshot.error}'),
            );
          }
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final jobs = snapshot.data!;
          if (jobs.isEmpty) {
            return const Center(child: Text('No active jobs available yet.'));
          }
          return ListView.separated(
            padding: const EdgeInsets.all(20),
            itemCount: jobs.length,
            separatorBuilder: (context, index) => const SizedBox(height: 14),
            itemBuilder: (context, index) {
              final job = jobs[index];
              return _CandidateListCard(
                title: job.title,
                subtitle: '${job.department} • ${job.location}',
                trailing: job.status,
                onTap: () => Navigator.of(context).push(
                  PageRouteBuilder(
                    pageBuilder: (context, animation, secondaryAnimation) =>
                        JobDetailsScreen(job: job),
                    transitionDuration: Duration.zero,
                    reverseTransitionDuration: Duration.zero,
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

class JobDetailsScreen extends StatelessWidget {
  const JobDetailsScreen({super.key, required this.job});

  final JobItem job;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Job Details'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              job.title,
              style: GoogleFonts.poppins(
                fontSize: 28,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 20),
            _DetailBlock(label: 'Department', value: job.department),
            _DetailBlock(label: 'Required Skills', value: job.requiredSkills),
            _DetailBlock(label: 'Required Experience', value: job.experience),
            _DetailBlock(label: 'Education Requirement', value: job.education),
            _DetailBlock(label: 'Job Description', value: job.description),
            _DetailBlock(label: 'Location', value: job.location),
            _DetailBlock(label: 'Employment Type', value: job.employmentType),
            _DetailBlock(label: 'Salary Range', value: job.salaryRange),
            const SizedBox(height: 18),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => Navigator.of(context).push(
                  PageRouteBuilder(
                    pageBuilder: (context, animation, secondaryAnimation) =>
                        ResumeUploadScreen(job: job),
                    transitionDuration: Duration.zero,
                    reverseTransitionDuration: Duration.zero,
                  ),
                ),
                child: const Text('Apply Now'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class ResumeUploadScreen extends StatefulWidget {
  const ResumeUploadScreen({super.key, required this.job});

  final JobItem job;

  @override
  State<ResumeUploadScreen> createState() => _ResumeUploadScreenState();
}

class _ResumeUploadScreenState extends State<ResumeUploadScreen> {
  PlatformFile? _selectedFile;
  bool _isAnalyzing = false;
  String? _analysisMessage;
  ResumeScoreBreakdown? _breakdown;

  Future<void> _pickResume() async {
    final selection = await showDialog<_ResumeSelectionType>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Upload Resume'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                title: const Text('PDF'),
                subtitle: const Text('Select a PDF resume'),
                onTap: () =>
                    Navigator.of(dialogContext).pop(_ResumeSelectionType.pdf),
              ),
              ListTile(
                title: const Text('DOC or DOCX'),
                subtitle: const Text('Select a DOC or DOCX resume'),
                onTap: () =>
                    Navigator.of(dialogContext).pop(_ResumeSelectionType.docx),
              ),
            ],
          ),
        );
      },
    );

    if (selection == null) {
      return;
    }

    final selectedExtension = selection == _ResumeSelectionType.pdf
        ? <String>['pdf']
        : <String>['doc', 'docx'];

    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: selectedExtension,
      allowMultiple: false,
      withData: true,
    );

    if (!mounted || result == null || result.files.isEmpty) {
      return;
    }

    final pickedFile = result.files.single;
    final extension = pickedFile.extension?.toLowerCase();
    if (pickedFile.bytes == null ||
        extension == null ||
        !selectedExtension.contains(extension)) {
      return;
    }

    setState(() {
      _selectedFile = pickedFile;
      _analysisMessage = null;
      _breakdown = null;
    });
  }

  void _removeSelectedFile() {
    if (_isAnalyzing) {
      return;
    }

    setState(() {
      _selectedFile = null;
      _analysisMessage = null;
      _breakdown = null;
    });
  }

  Future<void> _submitApplication() async {
    if (_selectedFile == null) {
      setState(
        () => _analysisMessage =
            'Please upload a PDF, DOC, or DOCX resume first.',
      );
      return;
    }

    if (_isAnalyzing) {
      return;
    }

    setState(() {
      _isAnalyzing = true;
      _analysisMessage = 'Uploading Resume...';
      _breakdown = null;
    });

    try {
      final user = FirebaseAuth.instance.currentUser;
      debugPrint('=== APPLICATION SUBMIT START ===');
      debugPrint('Application submit auth uid: ${user?.uid}');
      debugPrint('Application submit auth email: ${user?.email}');
      debugPrint('Application submit jobId: ${widget.job.id}');
      await FirestoreService.createApplication(
        job: widget.job,
        resumeFileName: _selectedFile!.name,
      );
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _isAnalyzing = false;
        _analysisMessage = error.toString().replaceFirst('Bad state: ', '');
      });
      return;
    }

    if (!mounted) {
      return;
    }

    setState(() {
      _isAnalyzing = false;
      _analysisMessage = 'Application submitted successfully.';
      _breakdown = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Resume Upload'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Apply for ${widget.job.title}',
              style: GoogleFonts.poppins(
                fontSize: 24,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _isAnalyzing ? null : _pickResume,
              child: const Text('Upload Resume Button'),
            ),
            const SizedBox(height: 12),
            if (_selectedFile != null) ...[
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFFE7EDF6)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Selected Resume:',
                      style: GoogleFonts.poppins(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 8),
                    Text(_selectedFile!.name),
                    Text(_formatFileSize(_selectedFile!.size)),
                    Text(_selectedFileTypeLabel(_selectedFile!)),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      onPressed: _isAnalyzing ? null : _pickResume,
                      child: const Text('Change File button'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _isAnalyzing ? null : _removeSelectedFile,
                      child: const Text('Remove File button'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 18),
            ],
            ElevatedButton(
              onPressed: _isAnalyzing || _selectedFile == null
                  ? null
                  : _submitApplication,
              child: const Text('Submit Application Button'),
            ),
            const SizedBox(height: 20),
            if (_isAnalyzing) const Center(child: CircularProgressIndicator()),
            if (_analysisMessage != null) ...[
              const SizedBox(height: 12),
              Text(
                _analysisMessage!,
                style: GoogleFonts.poppins(fontWeight: FontWeight.w700),
              ),
            ],
            if (_breakdown != null) ...[
              const SizedBox(height: 12),
              _ResultLine(
                label: 'Skills Score',
                value: '${_breakdown!.skillsScore}%',
              ),
              _ResultLine(
                label: 'Experience Score',
                value: '${_breakdown!.experienceScore}%',
              ),
              _ResultLine(
                label: 'Education Score',
                value: '${_breakdown!.educationScore}%',
              ),
              _ResultLine(
                label: 'Projects Score',
                value: '${_breakdown!.projectsScore}%',
              ),
              const SizedBox(height: 12),
              _ResultLine(
                label: 'Final Resume Score',
                value: '${_breakdown!.finalScore}%',
              ),
              _ResultLine(label: 'Application Status', value: 'Applied'),
            ],
          ],
        ),
      ),
    );
  }

  String _formatFileSize(int bytes) {
    const kilobyte = 1024;
    const megabyte = kilobyte * 1024;

    if (bytes >= megabyte) {
      return '${(bytes / megabyte).toStringAsFixed(1)} MB';
    }

    if (bytes >= kilobyte) {
      return '${(bytes / kilobyte).toStringAsFixed(1)} KB';
    }

    return '$bytes B';
  }

  String _selectedFileTypeLabel(PlatformFile file) {
    final extension = file.extension?.toUpperCase();
    if (extension == null || extension.isEmpty) {
      return 'Unknown File Type';
    }

    return '$extension Document';
  }
}

enum _ResumeSelectionType { pdf, docx }

class MyApplicationsScreen extends StatelessWidget {
  const MyApplicationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('My Applications'),
      ),
      body: StreamBuilder<List<ApplicationRecord>>(
        stream: FirestoreService.candidateApplications(),
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(
              child: Text('Could not load applications: ${snapshot.error}'),
            );
          }
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final applications = snapshot.data!;
          if (applications.isEmpty) {
            return const Center(child: Text('No applications submitted yet.'));
          }

          return ListView.separated(
            padding: const EdgeInsets.all(20),
            itemCount: applications.length,
            separatorBuilder: (context, index) => const SizedBox(height: 14),
            itemBuilder: (context, index) {
              final application = applications[index];
              return _ApplicationCard(application: application);
            },
          );
        },
      ),
    );
  }
}

class _ApplicationCard extends StatelessWidget {
  const _ApplicationCard({required this.application});

  final ApplicationRecord application;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFE7EDF6)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            application.jobTitle,
            style: GoogleFonts.poppins(
              fontSize: 20,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 8),
          Text('Resume Score: ${application.resumeScore ?? 'Pending'}'),
          Text('Current Status: ${application.status}'),
          Text('Application Date: ${_formatDate(application.submittedAt)}'),
          if (application.status == 'Interview Scheduled') ...[
            const SizedBox(height: 8),
            Text('Interview Date: ${application.interviewDate ?? ''}'),
            Text('Interview Time: ${application.interviewTime ?? ''}'),
            Text('Interview Platform: ${application.interviewPlatform ?? ''}'),
            Text('Meeting Link: ${application.meetingLink ?? ''}'),
          ],
        ],
      ),
    );
  }

  String _formatDate(DateTime dateTime) {
    return '${dateTime.day} ${_monthName(dateTime.month)} ${dateTime.year}';
  }

  String _monthName(int month) {
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
    return months[month - 1];
  }
}

class _CandidateListCard extends StatelessWidget {
  const _CandidateListCard({
    required this.title,
    required this.subtitle,
    required this.trailing,
    required this.onTap,
  });

  final String title;
  final String subtitle;
  final String trailing;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0xFFE7EDF6)),
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: GoogleFonts.poppins(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(subtitle),
                  ],
                ),
              ),
              Text(
                trailing,
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DetailBlock extends StatelessWidget {
  const _DetailBlock({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE7EDF6)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(
              fontWeight: FontWeight.w700,
              color: Color(0xFF64748B),
            ),
          ),
          const SizedBox(height: 6),
          Text(value),
        ],
      ),
    );
  }
}

class _ResultLine extends StatelessWidget {
  const _ResultLine({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w800)),
        ],
      ),
    );
  }
}
