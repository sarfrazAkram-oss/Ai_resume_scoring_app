import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class RecruiterLocalStore {
  RecruiterLocalStore._();

  static final ValueNotifier<int> jobCount = ValueNotifier<int>(0);
}

class JobManagementScreen extends StatefulWidget {
  const JobManagementScreen({super.key});

  @override
  State<JobManagementScreen> createState() => _JobManagementScreenState();
}

class _JobManagementScreenState extends State<JobManagementScreen> {
  late List<JobItem> _jobs;

  @override
  void initState() {
    super.initState();
    _jobs = [
      const JobItem(
        title: 'AI Engineer',
        department: 'AI Team',
        requiredSkills: 'Python, ML, NLP',
        experience: '2+ Years',
        education: 'BS in Computer Science',
        description: 'Build and optimize AI features for the hiring platform.',
        location: 'Remote',
        employmentType: 'Full-time',
        salaryRange: '80k - 110k',
        applicants: 15,
        status: 'Open',
      ),
      const JobItem(
        title: 'Flutter Developer',
        department: 'Product Team',
        requiredSkills: 'Flutter, Dart, UI',
        experience: '3+ Years',
        education: 'BS in Software Engineering',
        description:
            'Develop polished mobile experiences for recruiters and candidates.',
        location: 'Lahore',
        employmentType: 'Full-time',
        salaryRange: '60k - 90k',
        applicants: 10,
        status: 'Open',
      ),
      const JobItem(
        title: 'HR Coordinator',
        department: 'Human Resources',
        requiredSkills: 'Communication, Scheduling, ATS',
        experience: '1+ Years',
        education: 'Bachelor\'s Degree',
        description: 'Coordinate candidate flow and hiring operations.',
        location: 'Karachi',
        employmentType: 'Contract',
        salaryRange: '40k - 55k',
        applicants: 8,
        status: 'Closed',
      ),
    ];
    RecruiterLocalStore.jobCount.value = _jobs.length;
  }

  Future<void> _openCreateJob() async {
    final createdJob = await Navigator.of(context).push<JobItem>(
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) =>
            const CreateJobScreen(),
        transitionDuration: Duration.zero,
        reverseTransitionDuration: Duration.zero,
      ),
    );

    if (createdJob == null) {
      return;
    }

    setState(() {
      _jobs = [createdJob, ..._jobs];
    });
    RecruiterLocalStore.jobCount.value = _jobs.length;

    if (!mounted) {
      return;
    }

    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Job created successfully.')));
  }

  Future<void> _editJob(int index) async {
    final updatedJob = await Navigator.of(context).push<JobItem>(
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) =>
            CreateJobScreen(initialJob: _jobs[index]),
        transitionDuration: Duration.zero,
        reverseTransitionDuration: Duration.zero,
      ),
    );

    if (updatedJob == null) {
      return;
    }

    setState(() {
      _jobs[index] = updatedJob;
    });
  }

  Future<void> _deleteJob(int index) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Delete Job'),
          content: const Text('Are you sure you want to delete this job?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(true),
              child: const Text('Delete'),
            ),
          ],
        );
      },
    );

    if (confirmed != true) {
      return;
    }

    setState(() {
      _jobs.removeAt(index);
    });
    RecruiterLocalStore.jobCount.value = _jobs.length;
  }

  void _viewJob(JobItem job) {
    Navigator.of(context).push(
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) =>
            JobDetailsScreen(job: job),
        transitionDuration: Duration.zero,
        reverseTransitionDuration: Duration.zero,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return RecruiterModuleShell(
      title: 'Job Management',
      subtitle: 'Create, manage, and review current job postings.',
      actionLabel: 'Create Job',
      actionIcon: Icons.add_rounded,
      actionOnPressed: _openCreateJob,
      children: [
        const SizedBox(height: 24),
        ...List.generate(
          _jobs.length,
          (index) => Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: JobCard(
              job: _jobs[index],
              onEdit: () => _editJob(index),
              onDelete: () => _deleteJob(index),
              onViewDetails: () => _viewJob(_jobs[index]),
            ),
          ),
        ),
      ],
    );
  }
}

class CreateJobScreen extends StatefulWidget {
  const CreateJobScreen({super.key, this.initialJob});

  final JobItem? initialJob;

  @override
  State<CreateJobScreen> createState() => _CreateJobScreenState();
}

class _CreateJobScreenState extends State<CreateJobScreen> {
  late final TextEditingController _titleController;
  late final TextEditingController _departmentController;
  late final TextEditingController _skillsController;
  late final TextEditingController _experienceController;
  late final TextEditingController _educationController;
  late final TextEditingController _descriptionController;
  late final TextEditingController _locationController;
  late final TextEditingController _employmentTypeController;
  late final TextEditingController _salaryRangeController;
  late final TextEditingController _applicantsController;
  late String _status;

  @override
  void initState() {
    super.initState();
    final job = widget.initialJob;
    _titleController = TextEditingController(text: job?.title ?? '');
    _departmentController = TextEditingController(text: job?.department ?? '');
    _skillsController = TextEditingController(text: job?.requiredSkills ?? '');
    _experienceController = TextEditingController(text: job?.experience ?? '');
    _educationController = TextEditingController(text: job?.education ?? '');
    _descriptionController = TextEditingController(
      text: job?.description ?? '',
    );
    _locationController = TextEditingController(text: job?.location ?? '');
    _employmentTypeController = TextEditingController(
      text: job?.employmentType ?? '',
    );
    _salaryRangeController = TextEditingController(
      text: job?.salaryRange ?? '',
    );
    _applicantsController = TextEditingController(
      text: job?.applicants.toString() ?? '0',
    );
    _status = job?.status ?? 'Open';
  }

  @override
  void dispose() {
    _titleController.dispose();
    _departmentController.dispose();
    _skillsController.dispose();
    _experienceController.dispose();
    _educationController.dispose();
    _descriptionController.dispose();
    _locationController.dispose();
    _employmentTypeController.dispose();
    _salaryRangeController.dispose();
    _applicantsController.dispose();
    super.dispose();
  }

  void _saveJob() {
    final job = JobItem(
      title: _titleController.text.trim(),
      department: _departmentController.text.trim(),
      requiredSkills: _skillsController.text.trim(),
      experience: _experienceController.text.trim(),
      education: _educationController.text.trim(),
      description: _descriptionController.text.trim(),
      location: _locationController.text.trim(),
      employmentType: _employmentTypeController.text.trim(),
      salaryRange: _salaryRangeController.text.trim(),
      applicants: int.tryParse(_applicantsController.text.trim()) ?? 0,
      status: _status,
    );

    Navigator.of(context).pop(job);
  }

  @override
  Widget build(BuildContext context) {
    final isEditing = widget.initialJob != null;

    return RecruiterModuleShell(
      title: isEditing ? 'Edit Job' : 'Create Job',
      subtitle: isEditing
          ? 'Update the existing job details.'
          : 'Fill in the placeholder job posting form.',
      actionLabel: isEditing ? 'Save / Update' : 'Submit',
      actionIcon: isEditing ? Icons.save_rounded : Icons.send_rounded,
      actionOnPressed: _saveJob,
      children: [
        const SizedBox(height: 24),
        JobFormField(controller: _titleController, label: 'Job Title'),
        JobFormField(controller: _departmentController, label: 'Department'),
        JobFormField(
          controller: _skillsController,
          label: 'Required Skills',
          maxLines: 2,
        ),
        JobFormField(
          controller: _experienceController,
          label: 'Required Experience',
        ),
        JobFormField(
          controller: _educationController,
          label: 'Education Requirement',
        ),
        JobFormField(
          controller: _descriptionController,
          label: 'Job Description',
          maxLines: 4,
        ),
        JobFormField(controller: _locationController, label: 'Location'),
        JobFormField(
          controller: _employmentTypeController,
          label: 'Employment Type',
        ),
        JobFormField(controller: _salaryRangeController, label: 'Salary Range'),
        JobFormField(
          controller: _applicantsController,
          label: 'Number of Applicants',
        ),
        const SizedBox(height: 6),
        DropdownButtonFormField<String>(
          initialValue: _status,
          items: const [
            DropdownMenuItem(value: 'Open', child: Text('Open')),
            DropdownMenuItem(value: 'Closed', child: Text('Closed')),
          ],
          onChanged: (value) {
            if (value != null) {
              setState(() {
                _status = value;
              });
            }
          },
          decoration: InputDecoration(
            labelText: 'Job Status',
            filled: true,
            fillColor: Colors.white,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
          ),
        ),
      ],
    );
  }
}

class JobDetailsScreen extends StatelessWidget {
  const JobDetailsScreen({super.key, required this.job});

  final JobItem job;

  @override
  Widget build(BuildContext context) {
    return RecruiterModuleShell(
      title: 'Job Details',
      subtitle: job.title,
      actionLabel: 'Back',
      actionIcon: Icons.arrow_back_rounded,
      actionOnPressed: () => Navigator.of(context).pop(),
      children: [
        const SizedBox(height: 24),
        DetailTile(label: 'Job Title', value: job.title),
        DetailTile(label: 'Department', value: job.department),
        DetailTile(label: 'Required Skills', value: job.requiredSkills),
        DetailTile(label: 'Experience', value: job.experience),
        DetailTile(label: 'Education', value: job.education),
        DetailTile(label: 'Job Description', value: job.description),
        DetailTile(label: 'Location', value: job.location),
        DetailTile(label: 'Employment Type', value: job.employmentType),
        DetailTile(label: 'Salary Range', value: job.salaryRange),
        DetailTile(label: 'Job Status', value: job.status),
      ],
    );
  }
}

class JobItem {
  const JobItem({
    required this.title,
    required this.department,
    required this.requiredSkills,
    required this.experience,
    required this.education,
    required this.description,
    required this.location,
    required this.employmentType,
    required this.salaryRange,
    required this.applicants,
    required this.status,
  });

  final String title;
  final String department;
  final String requiredSkills;
  final String experience;
  final String education;
  final String description;
  final String location;
  final String employmentType;
  final String salaryRange;
  final int applicants;
  final String status;
}

class JobCard extends StatelessWidget {
  const JobCard({
    super.key,
    required this.job,
    required this.onEdit,
    required this.onDelete,
    required this.onViewDetails,
  });

  final JobItem job;
  final VoidCallback onEdit;
  final VoidCallback onDelete;
  final VoidCallback onViewDetails;

  @override
  Widget build(BuildContext context) {
    final isOpen = job.status.toLowerCase() == 'open';

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFFE7EDF6)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      job.title,
                      style: GoogleFonts.poppins(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: const Color(0xFF0F172A),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text('Department: ${job.department}'),
                    Text('Required Experience: ${job.experience}'),
                    Text('Number of Applicants: ${job.applicants}'),
                    Text('Job Status: ${job.status}'),
                  ],
                ),
              ),
              StatusPill(label: job.status, active: isOpen),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              ActionChipButton(
                label: 'Edit',
                color: const Color(0xFF2563EB),
                onTap: onEdit,
              ),
              ActionChipButton(
                label: 'Delete',
                color: const Color(0xFFDC2626),
                onTap: onDelete,
              ),
              ActionChipButton(
                label: 'View Details',
                color: const Color(0xFF16A34A),
                onTap: onViewDetails,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class DetailTile extends StatelessWidget {
  const DetailTile({super.key, required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
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
            label,
            style: GoogleFonts.poppins(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: const Color(0xFF64748B),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            value,
            style: GoogleFonts.poppins(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: const Color(0xFF0F172A),
            ),
          ),
        ],
      ),
    );
  }
}

class JobFormField extends StatelessWidget {
  const JobFormField({
    super.key,
    required this.controller,
    required this.label,
    this.maxLines = 1,
  });

  final TextEditingController controller;
  final String label;
  final int maxLines;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: TextField(
        controller: controller,
        maxLines: maxLines,
        decoration: InputDecoration(
          labelText: label,
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
    );
  }
}

class StatusPill extends StatelessWidget {
  const StatusPill({super.key, required this.label, required this.active});

  final String label;
  final bool active;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: active ? const Color(0xFFEAF8F3) : const Color(0xFFFEECEC),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: active ? const Color(0xFF167A5C) : const Color(0xFFB91C1C),
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class ActionChipButton extends StatelessWidget {
  const ActionChipButton({
    super.key,
    required this.label,
    required this.color,
    required this.onTap,
  });

  final String label;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ActionChip(
      label: Text(label),
      backgroundColor: color.withValues(alpha: 0.08),
      labelStyle: TextStyle(color: color, fontWeight: FontWeight.w700),
      onPressed: onTap,
    );
  }
}

class RecruiterModuleShell extends StatelessWidget {
  const RecruiterModuleShell({
    super.key,
    required this.title,
    required this.subtitle,
    required this.actionLabel,
    required this.actionIcon,
    required this.actionOnPressed,
    required this.children,
    this.floatingActionButton,
  });

  final String title;
  final String subtitle;
  final String actionLabel;
  final IconData actionIcon;
  final VoidCallback actionOnPressed;
  final List<Widget> children;
  final Widget? floatingActionButton;

  @override
  Widget build(BuildContext context) {
    final baseTextTheme = Theme.of(context).textTheme;

    return Theme(
      data: Theme.of(
        context,
      ).copyWith(textTheme: GoogleFonts.poppinsTextTheme(baseTextTheme)),
      child: Scaffold(
        backgroundColor: const Color(0xFFF7F8FC),
        floatingActionButton: floatingActionButton,
        appBar: AppBar(
          backgroundColor: Colors.white,
          surfaceTintColor: Colors.white,
          elevation: 0,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back_rounded),
            onPressed: () => Navigator.of(context).maybePop(),
          ),
          title: Text(title),
        ),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                ModuleTopBar(
                  title: title,
                  subtitle: subtitle,
                  showAppBarSpacer: true,
                ),
                const SizedBox(height: 20),
                ElevatedButton.icon(
                  onPressed: actionOnPressed,
                  icon: Icon(actionIcon),
                  label: Text(actionLabel),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF2563EB),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 18,
                      vertical: 14,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                ),
                ...children,
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class ModuleTopBar extends StatelessWidget {
  const ModuleTopBar({
    super.key,
    required this.title,
    required this.subtitle,
    this.showAppBarSpacer = false,
  });

  final String title;
  final String subtitle;
  final bool showAppBarSpacer;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (showAppBarSpacer) const SizedBox(width: 8),
        Container(
          width: 56,
          height: 56,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF2563EB).withValues(alpha: 0.12),
                blurRadius: 18,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: const Icon(Icons.dashboard_outlined, color: Color(0xFF2563EB)),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: GoogleFonts.poppins(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: const Color(0xFF0F172A),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: GoogleFonts.poppins(
                  fontSize: 14,
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

class InfoCard extends StatelessWidget {
  const InfoCard({super.key, required this.child, required this.accentColor});

  final Widget child;
  final Color accentColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFFE7EDF6)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: child,
    );
  }
}

class InfoStyles {
  static TextStyle get title => GoogleFonts.poppins(
    fontSize: 22,
    fontWeight: FontWeight.w700,
    color: const Color(0xFF0F172A),
  );
}

class PillAction extends StatelessWidget {
  const PillAction({super.key, required this.label, this.danger = false});

  final String label;
  final bool danger;

  @override
  Widget build(BuildContext context) {
    final color = danger ? const Color(0xFFDC2626) : const Color(0xFF2563EB);
    return ActionChip(
      label: Text(label),
      onPressed: () {},
      backgroundColor: color.withValues(alpha: 0.08),
      labelStyle: TextStyle(color: color, fontWeight: FontWeight.w700),
    );
  }
}
