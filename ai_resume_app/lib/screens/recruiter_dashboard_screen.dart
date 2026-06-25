import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class RecruiterDashboardScreen extends StatelessWidget {
  const RecruiterDashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final baseTextTheme = Theme.of(context).textTheme;

    return Theme(
      data: Theme.of(
        context,
      ).copyWith(textTheme: GoogleFonts.poppinsTextTheme(baseTextTheme)),
      child: Scaffold(
        backgroundColor: const Color(0xFFF7F8FC),
        body: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFFF8FBFF), Color(0xFFF2F6FB)],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
            ),
          ),
          child: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: TweenAnimationBuilder<double>(
                tween: Tween<double>(begin: 0, end: 1),
                duration: const Duration(milliseconds: 600),
                curve: Curves.easeOutCubic,
                builder: (context, value, child) {
                  return Opacity(
                    opacity: value,
                    child: Transform.translate(
                      offset: Offset(0, 18 * (1 - value)),
                      child: child,
                    ),
                  );
                },
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final width = constraints.maxWidth;
                    final cardWidth = width >= 960
                        ? (width - 36) / 2
                        : width >= 620
                        ? (width - 18) / 2
                        : width;

                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _RecruiterHeader(width: width),
                        const SizedBox(height: 24),
                        Wrap(
                          spacing: 18,
                          runSpacing: 18,
                          children: [
                            SizedBox(
                              width: cardWidth,
                              child: _RecruiterFeatureCard(
                                title: 'Job Management',
                                subtitle:
                                    'Create, edit, delete, and view jobs from one place.',
                                icon: Icons.work_outline_rounded,
                                accentColor: const Color(0xFF2563EB),
                                gradient: const LinearGradient(
                                  colors: [
                                    Color(0xFFF8FBFF),
                                    Color(0xFFEEF4FF),
                                  ],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                details: const [
                                  'Create Job',
                                  'Edit Job',
                                  'Delete Job',
                                  'View Jobs',
                                ],
                              ),
                            ),
                            SizedBox(
                              width: cardWidth,
                              child: _RecruiterFeatureCard(
                                title: 'Applications',
                                subtitle: 'View all candidate applications.',
                                icon: Icons.assignment_turned_in_outlined,
                                accentColor: const Color(0xFF7C3AED),
                                gradient: const LinearGradient(
                                  colors: [
                                    Color(0xFFFCF7FF),
                                    Color(0xFFF4ECFF),
                                  ],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                details: const [
                                  'View all candidate applications',
                                ],
                              ),
                            ),
                            SizedBox(
                              width: cardWidth,
                              child: _RecruiterFeatureCard(
                                title: 'Candidates',
                                subtitle:
                                    'View ranked candidates for each job.',
                                icon: Icons.groups_2_outlined,
                                accentColor: const Color(0xFF167A5C),
                                gradient: const LinearGradient(
                                  colors: [
                                    Color(0xFFF3FFF7),
                                    Color(0xFFECFFF3),
                                  ],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                details: const [
                                  'View ranked candidates for each job',
                                ],
                              ),
                            ),
                            SizedBox(
                              width: cardWidth,
                              child: _RecruiterFeatureCard(
                                title: 'Interviews',
                                subtitle: 'Schedule and manage interviews.',
                                icon: Icons.event_note_outlined,
                                accentColor: const Color(0xFF0F766E),
                                gradient: const LinearGradient(
                                  colors: [
                                    Color(0xFFF6FFFE),
                                    Color(0xFFE8FBF8),
                                  ],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                details: const [
                                  'Schedule interviews',
                                  'Manage interview status',
                                ],
                              ),
                            ),
                            SizedBox(
                              width: cardWidth,
                              child: _RecruiterFeatureCard(
                                title: 'Analytics',
                                subtitle:
                                    'View hiring statistics and recruitment insights.',
                                icon: Icons.analytics_outlined,
                                accentColor: const Color(0xFFEA580C),
                                gradient: const LinearGradient(
                                  colors: [
                                    Color(0xFFFFF8F3),
                                    Color(0xFFFFF1E8),
                                  ],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                details: const [
                                  'View hiring statistics',
                                  'Review recruitment insights',
                                ],
                              ),
                            ),
                          ],
                        ),
                      ],
                    );
                  },
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _RecruiterHeader extends StatelessWidget {
  const _RecruiterHeader({required this.width});

  final double width;

  @override
  Widget build(BuildContext context) {
    final titleSize = width >= 900
        ? 32.0
        : width >= 520
        ? 28.0
        : 24.0;
    final subtitleSize = width >= 520 ? 16.0 : 14.0;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 60,
          height: 60,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF167A5C).withValues(alpha: 0.14),
                blurRadius: 20,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: const Icon(
            Icons.badge_outlined,
            color: Color(0xFF167A5C),
            size: 34,
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Recruiter Dashboard',
                style: GoogleFonts.poppins(
                  fontSize: titleSize,
                  fontWeight: FontWeight.w800,
                  color: const Color(0xFF0F172A),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Manage hiring activity and candidate progress',
                style: GoogleFonts.poppins(
                  fontSize: subtitleSize,
                  fontWeight: FontWeight.w600,
                  color: const Color(0xFF167A5C),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'Temporary recruiter workspace for testing navigation and layout only.',
                style: GoogleFonts.poppins(
                  fontSize: subtitleSize,
                  height: 1.5,
                  fontWeight: FontWeight.w500,
                  color: const Color(0xFF64748B),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _RecruiterFeatureCard extends StatelessWidget {
  const _RecruiterFeatureCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.accentColor,
    required this.gradient,
    required this.details,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final Color accentColor;
  final Gradient gradient;
  final List<String> details;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: gradient,
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: Colors.white.withValues(alpha: 0.7)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 25,
            spreadRadius: 1,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(18),
              boxShadow: [
                BoxShadow(
                  color: accentColor.withValues(alpha: 0.16),
                  blurRadius: 16,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: Icon(icon, color: accentColor, size: 34),
          ),
          const SizedBox(height: 18),
          Text(
            title,
            style: GoogleFonts.poppins(
              fontSize: 24,
              fontWeight: FontWeight.w700,
              color: const Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            subtitle,
            style: GoogleFonts.poppins(
              fontSize: 15,
              height: 1.5,
              fontWeight: FontWeight.w500,
              color: const Color(0xFF475569),
            ),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: details
                .map(
                  (detail) => Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 10,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.78),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: accentColor.withValues(alpha: 0.12),
                      ),
                    ),
                    child: Text(
                      detail,
                      style: GoogleFonts.poppins(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: const Color(0xFF334155),
                      ),
                    ),
                  ),
                )
                .toList(),
          ),
        ],
      ),
    );
  }
}
