import 'package:flutter/material.dart';

import 'job_management_screen.dart';

class InterviewsScreen extends StatelessWidget {
  const InterviewsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return RecruiterModuleShell(
      title: 'Interviews',
      subtitle: 'Schedule and manage all upcoming interviews.',
      actionLabel: 'Back to Dashboard',
      actionIcon: Icons.arrow_back_rounded,
      actionOnPressed: () => Navigator.of(context).pop(),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          Navigator.of(context).push(
            PageRouteBuilder(
              pageBuilder: (context, animation, secondaryAnimation) =>
                  const ScheduleInterviewScreen(),
              transitionDuration: Duration.zero,
              reverseTransitionDuration: Duration.zero,
            ),
          );
        },
        icon: const Icon(Icons.add_rounded),
        label: const Text('Schedule Interview'),
      ),
      children: [
        const SizedBox(height: 24),
        InfoCard(
          accentColor: const Color(0xFF0F766E),
          child: Text('No interviews scheduled yet.', style: InfoStyles.title),
        ),
      ],
    );
  }
}

class ScheduleInterviewScreen extends StatefulWidget {
  const ScheduleInterviewScreen({super.key});

  @override
  State<ScheduleInterviewScreen> createState() =>
      _ScheduleInterviewScreenState();
}

class _ScheduleInterviewScreenState extends State<ScheduleInterviewScreen> {
  late final TextEditingController _candidateController;
  late final TextEditingController _jobPositionController;
  late final TextEditingController _dateController;
  late final TextEditingController _timeController;
  late final TextEditingController _interviewTypeController;
  late final TextEditingController _meetingLinkController;
  late final TextEditingController _notesController;

  @override
  void initState() {
    super.initState();
    _candidateController = TextEditingController();
    _jobPositionController = TextEditingController();
    _dateController = TextEditingController();
    _timeController = TextEditingController();
    _interviewTypeController = TextEditingController();
    _meetingLinkController = TextEditingController();
    _notesController = TextEditingController();
  }

  @override
  void dispose() {
    _candidateController.dispose();
    _jobPositionController.dispose();
    _dateController.dispose();
    _timeController.dispose();
    _interviewTypeController.dispose();
    _meetingLinkController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return RecruiterModuleShell(
      title: 'Schedule Interview',
      subtitle: 'Placeholder interview scheduling form.',
      actionLabel: 'Back',
      actionIcon: Icons.arrow_back_rounded,
      actionOnPressed: () => Navigator.of(context).pop(),
      children: [
        SizedBox(height: 24),
        JobFormField(controller: _candidateController, label: 'Candidate'),
        JobFormField(controller: _jobPositionController, label: 'Job Position'),
        JobFormField(controller: _dateController, label: 'Date'),
        JobFormField(controller: _timeController, label: 'Time'),
        JobFormField(
          controller: _interviewTypeController,
          label: 'Interview Type',
        ),
        JobFormField(controller: _meetingLinkController, label: 'Meeting Link'),
        JobFormField(controller: _notesController, label: 'Notes', maxLines: 3),
      ],
    );
  }
}
