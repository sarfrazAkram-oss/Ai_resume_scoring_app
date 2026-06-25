import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'job_management_screen.dart';

class AnalyticsScreen extends StatelessWidget {
  const AnalyticsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<int>(
      valueListenable: RecruiterLocalStore.jobCount,
      builder: (context, jobCount, _) {
        final stats = <_StatItem>[
          _StatItem(
            label: 'Total Jobs Posted',
            value: '$jobCount',
            icon: Icons.work_outline_rounded,
            color: const Color(0xFF2563EB),
          ),
          const _StatItem(
            label: 'Total Applications',
            value: '0',
            icon: Icons.description_outlined,
            color: Color(0xFF7C3AED),
          ),
          const _StatItem(
            label: 'Total Candidates',
            value: '0',
            icon: Icons.groups_2_outlined,
            color: Color(0xFF167A5C),
          ),
          const _StatItem(
            label: 'Interviews Scheduled',
            value: '0',
            icon: Icons.event_note_outlined,
            color: Color(0xFF0F766E),
          ),
          const _StatItem(
            label: 'Candidates Hired',
            value: '0',
            icon: Icons.verified_outlined,
            color: Color(0xFF16A34A),
          ),
          const _StatItem(
            label: 'Candidates Rejected',
            value: '0',
            icon: Icons.block_outlined,
            color: Color(0xFFEA580C),
          ),
        ];

        return RecruiterModuleShell(
          title: 'Analytics',
          subtitle: 'Recruitment statistics and placeholder insights.',
          actionLabel: 'Back to Dashboard',
          actionIcon: Icons.arrow_back_rounded,
          actionOnPressed: () => Navigator.of(context).pop(),
          children: [
            const SizedBox(height: 24),
            Wrap(
              spacing: 16,
              runSpacing: 16,
              children: stats
                  .map(
                    (stat) =>
                        SizedBox(width: 220, child: _StatCard(stat: stat)),
                  )
                  .toList(),
            ),
            const SizedBox(height: 24),
            const Row(
              children: [
                Expanded(child: _ChartPlaceholder(title: 'Applications Trend')),
                SizedBox(width: 16),
                Expanded(child: _ChartPlaceholder(title: 'Hiring Funnel')),
              ],
            ),
          ],
        );
      },
    );
  }
}

class _StatItem {
  const _StatItem({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  final String label;
  final String value;
  final IconData icon;
  final Color color;
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.stat});

  final _StatItem stat;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE7EDF6)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: stat.color.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(stat.icon, color: stat.color),
          ),
          const SizedBox(height: 18),
          Text(
            stat.value,
            style: GoogleFonts.poppins(
              fontSize: 28,
              fontWeight: FontWeight.w800,
              color: const Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            stat.label,
            style: GoogleFonts.poppins(
              fontSize: 14,
              color: const Color(0xFF64748B),
            ),
          ),
        ],
      ),
    );
  }
}

class _ChartPlaceholder extends StatelessWidget {
  const _ChartPlaceholder({required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 220,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE7EDF6)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: GoogleFonts.poppins(fontWeight: FontWeight.w700)),
          const SizedBox(height: 18),
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFFF8FBFF), Color(0xFFEEF4FF)],
                ),
                borderRadius: BorderRadius.circular(18),
              ),
              child: const Center(
                child: Icon(
                  Icons.bar_chart_rounded,
                  size: 56,
                  color: Color(0xFF2563EB),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
