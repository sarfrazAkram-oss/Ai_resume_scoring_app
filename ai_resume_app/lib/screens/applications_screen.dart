import 'package:flutter/material.dart';

import 'job_management_screen.dart';

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
        InfoCard(
          accentColor: const Color(0xFF7C3AED),
          child: Text(
            'No applications available yet.',
            style: InfoStyles.title,
          ),
        ),
      ],
    );
  }
}
