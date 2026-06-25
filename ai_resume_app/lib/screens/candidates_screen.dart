import 'package:flutter/material.dart';

import 'job_management_screen.dart';

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
        InfoCard(
          accentColor: const Color(0xFF167A5C),
          child: Text('No candidates available yet.', style: InfoStyles.title),
        ),
      ],
    );
  }
}
