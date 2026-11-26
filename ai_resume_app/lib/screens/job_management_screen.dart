import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../services/firestore_service.dart';
import 'local_resume_store.dart';

class JobManagementScreen extends StatefulWidget {
  const JobManagementScreen({super.key});

  @override
  State<JobManagementScreen> createState() => _JobManagementScreenState();
}

class _JobManagementScreenState extends State<JobManagementScreen> {
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

    try {
      await FirestoreService.createJob(createdJob);
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Could not create job: $error')));
      return;
    }

    if (!mounted) {
      return;
    }

    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Job created successfully.')));
  }

  Future<void> _editJob(JobItem currentJob) async {
    final updatedJob = await Navigator.of(context).push<JobItem>(
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) =>
            CreateJobScreen(initialJob: currentJob),
        transitionDuration: Duration.zero,
        reverseTransitionDuration: Duration.zero,
      ),
    );

    if (updatedJob == null) {
      return;
    }

    try {
      await FirestoreService.updateJob(updatedJob);
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Could not update job: $error')));
    }
  }

  Future<void> _deleteJob(JobItem job) async {
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

    try {
      await FirestoreService.deleteJob(job);
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Could not delete job: $error')));
    }
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
        StreamBuilder<List<JobItem>>(
          stream: FirestoreService.recruiterJobs(),
          builder: (context, snapshot) {
            if (snapshot.hasError) {
              return InfoCard(
                accentColor: const Color(0xFFDC2626),
                child: Text('Could not load jobs: ${snapshot.error}'),
              );
            }
            if (!snapshot.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final jobs = snapshot.data!;
            if (jobs.isEmpty) {
              return InfoCard(
                accentColor: const Color(0xFF2563EB),
                child: Text('No jobs created yet.', style: InfoStyles.title),
              );
            }
            return Column(
              children: jobs
                  .map(
                    (job) => Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: JobCard(
                        job: job,
                        onEdit: () => _editJob(job),
                        onDelete: () => _deleteJob(job),
                        onViewDetails: () => _viewJob(job),
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

class CreateJobScreen extends StatefulWidget {
  const CreateJobScreen({super.key, this.initialJob});

  final JobItem? initialJob;

  @override
  State<CreateJobScreen> createState() => _CreateJobScreenState();
}

class _CreateJobScreenState extends State<CreateJobScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _titleController;
  late final TextEditingController _departmentController;
  late final TextEditingController _skillsController;
  late final TextEditingController _experienceController;
  late final TextEditingController _educationController;
  late final TextEditingController _descriptionController;
  late final TextEditingController _locationController;
  late final TextEditingController _employmentTypeController;
  late final TextEditingController _salaryRangeController;
  late final TextEditingController _jobTypeController;
  late final TextEditingController _skillsRequirementController;
  late final TextEditingController _experienceRequirementController;
  late final TextEditingController _experienceYearsController;
  late final TextEditingController _educationRequirementController;
  late final TextEditingController _projectsRequirementController;
  late final TextEditingController _projectCriteriaController;
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
    _jobTypeController = TextEditingController(
      text: job?.jobType ?? 'fresh_graduate',
    );
    _skillsRequirementController = TextEditingController(
      text: job?.skillsRequirement ?? 'required',
    );
    _experienceRequirementController = TextEditingController(
      text: job?.experienceRequirement ?? 'preferred',
    );
    _experienceYearsController = TextEditingController(
      text: job?.experienceYears ?? '',
    );
    _educationRequirementController = TextEditingController(
      text: job?.educationRequirement ?? 'required',
    );
    _projectsRequirementController = TextEditingController(
      text: job?.projectsRequirement ?? 'preferred',
    );
    _projectCriteriaController = TextEditingController(
      text: job?.projectCriteria ?? '',
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
    _jobTypeController.dispose();
    _skillsRequirementController.dispose();
    _experienceRequirementController.dispose();
    _experienceYearsController.dispose();
    _educationRequirementController.dispose();
    _projectsRequirementController.dispose();
    _projectCriteriaController.dispose();
    super.dispose();
  }

  void _saveJob() {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final experienceYearsValue = _experienceYearsController.text.trim();
    final policyVersion = widget.initialJob == null
        ? 2
        : widget.initialJob!.scoringPolicyVersion;
    final skillRequirement = _skillsRequirementController.text.trim();
    final experienceRequirement = _experienceRequirementController.text.trim();
    final educationRequirement = _educationRequirementController.text.trim();
    final projectsRequirement = _projectsRequirementController.text.trim();
    if (policyVersion == 2) {
      final states = {
        'Skills': skillRequirement,
        'Experience': experienceRequirement,
        'Education': educationRequirement,
        'Projects': projectsRequirement,
      };
      const validStates = {'required', 'preferred', 'not_applicable'};
      for (final entry in states.entries) {
        if (!validStates.contains(entry.value)) {
          _showValidationError(
            'Choose Required, Preferred, or Not applicable for ${entry.key}.',
          );
          return;
        }
      }

      final applicableCount = states.values
          .where((state) => state != 'not_applicable')
          .length;
      if (applicableCount == 0) {
        _showValidationError(
          'At least one scoring category must be applicable.',
        );
        return;
      }
      if (skillRequirement != 'not_applicable' &&
          !_hasMeaningfulCriteria(_skillsController.text)) {
        _showValidationError(
          'Enter at least one skill when Skills is applicable.',
        );
        return;
      }
      if (experienceRequirement != 'not_applicable') {
        final years = double.tryParse(experienceYearsValue);
        if (years == null || !years.isFinite || years <= 0) {
          _showValidationError(
            'Enter a positive number of experience years (for example, 0.5).',
          );
          return;
        }
      }
      if (educationRequirement != 'not_applicable' &&
          !_hasMeaningfulCriteria(_educationController.text)) {
        _showValidationError(
          'Enter an education criterion when Education is applicable.',
        );
        return;
      }
      if (projectsRequirement != 'not_applicable' &&
          !_hasMeaningfulCriteria(_projectCriteriaController.text)) {
        _showValidationError(
          'Enter explicit project criteria when Projects is applicable.',
        );
        return;
      }
    }

    final job = JobItem(
      id: widget.initialJob?.id,
      title: _titleController.text.trim(),
      department: _departmentController.text.trim(),
      requiredSkills: _skillsController.text.trim(),
      experience: _experienceController.text.trim(),
      education: _educationController.text.trim(),
      description: _descriptionController.text.trim(),
      location: _locationController.text.trim(),
      employmentType: _employmentTypeController.text.trim(),
      salaryRange: _salaryRangeController.text.trim(),
      applicants: widget.initialJob?.applicants ?? 0,
      status: _status,
      jobType: _jobTypeController.text.trim().isNotEmpty
          ? _jobTypeController.text.trim()
          : 'fresh_graduate',
      skillsRequirement: _skillsRequirementController.text.trim().isNotEmpty
          ? _skillsRequirementController.text.trim()
          : 'required',
      experienceRequirement:
          _experienceRequirementController.text.trim().isNotEmpty
          ? _experienceRequirementController.text.trim()
          : 'preferred',
      experienceYears: experienceYearsValue,
      educationRequirement:
          _educationRequirementController.text.trim().isNotEmpty
          ? _educationRequirementController.text.trim()
          : 'required',
      projectsRequirement: _projectsRequirementController.text.trim().isNotEmpty
          ? _projectsRequirementController.text.trim()
          : 'preferred',
      projectCriteria: _projectCriteriaController.text.trim(),
      scoringPolicyVersion: policyVersion,
    );

    Navigator.of(context).pop(job);
  }

  bool _hasMeaningfulCriteria(String value) =>
      RegExp(r'[A-Za-z0-9]').hasMatch(value.trim());

  void _showValidationError(String message) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  Widget _buildScoringPreview() {
    const componentWeights = <String, int>{
      'Skills': 40,
      'Experience': 25,
      'Education': 20,
      'Practical Work & Achievements': 15,
    };
    final applicability = <String, String>{
      'Skills': _skillsRequirementController.text,
      'Experience': _experienceRequirementController.text,
      'Education': _educationRequirementController.text,
      'Projects': _projectsRequirementController.text,
    };
    final validSelections = applicability.values.every(
      (state) =>
          const {'required', 'preferred', 'not_applicable'}.contains(state),
    );
    final hasApplicableCategory = applicability.values.any(
      (state) => state != 'not_applicable',
    );
    final years = double.tryParse(_experienceYearsController.text.trim());
    final validCriteria =
        (applicability['Skills'] == 'not_applicable' ||
            _hasMeaningfulCriteria(_skillsController.text)) &&
        (applicability['Experience'] == 'not_applicable' ||
            (years != null && years.isFinite && years > 0)) &&
        (applicability['Education'] == 'not_applicable' ||
            _hasMeaningfulCriteria(_educationController.text)) &&
        (applicability['Projects'] == 'not_applicable' ||
            _hasMeaningfulCriteria(_projectCriteriaController.text));
    final validPolicy =
        validSelections && hasApplicableCategory && validCriteria;

    return InfoCard(
      accentColor: const Color(0xFF2563EB),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Theme(
            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
            child: ExpansionTile(
              tilePadding: const EdgeInsets.symmetric(horizontal: 14),
              childrenPadding: const EdgeInsets.fromLTRB(14, 0, 14, 16),
              title: const Text(
                'Scoring Breakdown',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
              subtitle: const Text('Version 3 fixed component weights'),
              children: [
                for (final entry in componentWeights.entries)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 5),
                    child: Row(
                      children: [
                        Expanded(child: Text(entry.key)),
                        Text(switch (entry.key) {
                          'Skills'
                              when applicability['Skills'] ==
                                  'not_applicable' =>
                            '0 / ${entry.value} pts (N/A)',
                          'Experience'
                              when applicability['Experience'] ==
                                  'not_applicable' =>
                            '${entry.value} / ${entry.value} pts (neutral)',
                          'Education'
                              when applicability['Education'] ==
                                  'not_applicable' =>
                            '0 / ${entry.value} pts (N/A)',
                          'Practical Work & Achievements' =>
                            '${entry.value} pts (resume-wide evidence)',
                          _ => '${entry.value} pts',
                        }),
                      ],
                    ),
                  ),
                const Divider(),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    !validSelections
                        ? 'Select an applicability for every category.'
                        : !hasApplicableCategory
                        ? 'At least one category must be applicable.'
                        : validPolicy
                        ? 'Total possible: 100 points. N/A skills/education earn 0; N/A experience earns neutral full credit. Practical evidence is assessed across the resume.'
                        : 'Total possible: 100 points when applicability and required criteria are valid.',
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isEditing = widget.initialJob != null;
    final isLegacyEdit =
        isEditing && widget.initialJob!.scoringPolicyVersion == null;

    final experienceUiValue = switch (_experienceRequirementController.text) {
      'not_applicable' => 'none',
      'preferred' => 'preferred',
      _ => 'required',
    };
    final projectsUiValue = switch (_projectsRequirementController.text) {
      'not_applicable' => 'not_needed',
      'preferred' => 'optional',
      _ => 'required',
    };

    return RecruiterModuleShell(
      title: isEditing ? 'Edit Job' : 'Create Job',
      subtitle: isEditing
          ? 'Update the role details and candidate requirements.'
          : 'Create a clear role and define how candidates will be evaluated.',
      actionLabel: isEditing ? 'Save changes' : 'Publish job',
      actionIcon: isEditing ? Icons.save_rounded : Icons.send_rounded,
      actionOnPressed: _saveJob,
      showActionButton: false,
      children: [
        const SizedBox(height: 24),
        Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1040),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _JobFormSection(
                    number: '01',
                    title: 'Basic Job Details',
                    subtitle: 'Start with the role and where it is based.',
                    icon: Icons.work_outline_rounded,
                    child: Column(
                      children: [
                        _ResponsiveFieldRow(
                          first: JobFormField(
                            controller: _titleController,
                            label: 'Job title',
                            hintText: 'e.g. Product Designer',
                            required: true,
                            textInputAction: TextInputAction.next,
                          ),
                          second: JobFormField(
                            controller: _departmentController,
                            label: 'Department',
                            hintText: 'e.g. Product & Design',
                            textInputAction: TextInputAction.next,
                          ),
                        ),
                        if (!isLegacyEdit)
                          _ResponsiveFieldRow(
                            first: _JobSelectField<String>(
                              label: 'Job type',
                              value: _jobTypeController.text,
                              items: const [
                                DropdownMenuItem(
                                  value: 'internship',
                                  child: Text('Internship'),
                                ),
                                DropdownMenuItem(
                                  value: 'fresh_graduate',
                                  child: Text('Fresh Graduate / Entry Level'),
                                ),
                                DropdownMenuItem(
                                  value: 'experienced',
                                  child: Text('Experienced Professional'),
                                ),
                              ],
                              onChanged: (value) {
                                if (value != null) {
                                  setState(
                                    () => _jobTypeController.text = value,
                                  );
                                }
                              },
                            ),
                            second: JobFormField(
                              controller: _locationController,
                              label: 'Location',
                              hintText: 'City, region, or Remote',
                              required: true,
                              textInputAction: TextInputAction.next,
                            ),
                          )
                        else
                          JobFormField(
                            controller: _locationController,
                            label: 'Location',
                            hintText: 'City, region, or Remote',
                            required: true,
                          ),
                        _ResponsiveFieldRow(
                          first: JobFormField(
                            controller: _employmentTypeController,
                            label: 'Employment type',
                            hintText: 'e.g. Full-time',
                            textInputAction: TextInputAction.next,
                          ),
                          second: JobFormField(
                            controller: _salaryRangeController,
                            label: 'Salary range',
                            hintText: 'Optional',
                            textInputAction: TextInputAction.next,
                          ),
                        ),
                        _JobSelectField<String>(
                          label: 'Posting status',
                          value: _status,
                          items: const [
                            DropdownMenuItem(
                              value: 'Open',
                              child: Text('Open'),
                            ),
                            DropdownMenuItem(
                              value: 'Closed',
                              child: Text('Closed'),
                            ),
                          ],
                          onChanged: (value) {
                            if (value != null) {
                              setState(() => _status = value);
                            }
                          },
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  _JobFormSection(
                    number: '02',
                    title: 'Candidate Requirements',
                    subtitle:
                        'Set clear criteria. Only applicable categories count toward the score.',
                    icon: Icons.fact_check_outlined,
                    child: isLegacyEdit
                        ? Column(
                            children: [
                              JobFormField(
                                controller: _skillsController,
                                label: 'Required skills',
                                hintText: 'Separate skills with commas',
                                maxLines: 2,
                                textInputAction: TextInputAction.next,
                              ),
                              JobFormField(
                                controller: _educationController,
                                label: 'Education',
                                hintText: 'e.g. Bachelor’s in Computer Science',
                              ),
                              const _LegacyPolicyNotice(),
                            ],
                          )
                        : Column(
                            children: [
                              _ResponsiveFieldRow(
                                first: JobFormField(
                                  controller: _skillsController,
                                  label: 'Skills',
                                  hintText: 'e.g. Figma, user research',
                                  helperText:
                                      'Add the skills applicants should demonstrate.',
                                  maxLines: 2,
                                  required:
                                      _skillsRequirementController.text !=
                                      'not_applicable',
                                  textInputAction: TextInputAction.next,
                                  onChanged: () => setState(() {}),
                                  validator: (value) =>
                                      _skillsRequirementController.text ==
                                              'not_applicable' ||
                                          _hasMeaningfulCriteria(value ?? '')
                                      ? null
                                      : 'Add at least one skill.',
                                ),
                                second: JobFormField(
                                  controller: _educationController,
                                  label: 'Education',
                                  hintText: 'e.g. Bachelor’s degree in Design',
                                  helperText:
                                      'Enter the degree or qualification expected.',
                                  maxLines: 2,
                                  required:
                                      _educationRequirementController.text !=
                                      'not_applicable',
                                  textInputAction: TextInputAction.next,
                                  onChanged: () => setState(() {}),
                                  validator: (value) =>
                                      _educationRequirementController.text ==
                                              'not_applicable' ||
                                          _hasMeaningfulCriteria(value ?? '')
                                      ? null
                                      : 'Add an education criterion.',
                                ),
                              ),
                              _ResponsiveFieldRow(
                                first: _JobSelectField<String>(
                                  fieldKey: const ValueKey(
                                    'experience-selector',
                                  ),
                                  label: 'Experience',
                                  value: experienceUiValue,
                                  helperText: experienceUiValue == 'none'
                                      ? 'No experience required; this component receives neutral full credit.'
                                      : 'Experience is scored proportionally against the target.',
                                  items: const [
                                    DropdownMenuItem(
                                      value: 'none',
                                      child: Text(
                                        'None — No experience required',
                                      ),
                                    ),
                                    DropdownMenuItem(
                                      value: 'preferred',
                                      child: Text('Preferred'),
                                    ),
                                    DropdownMenuItem(
                                      value: 'required',
                                      child: Text('Required'),
                                    ),
                                  ],
                                  onChanged: (value) {
                                    if (value == null) return;
                                    setState(() {
                                      _experienceRequirementController.text =
                                          switch (value) {
                                            'none' => 'not_applicable',
                                            'preferred' => 'preferred',
                                            _ => 'required',
                                          };
                                    });
                                  },
                                ),
                                second: _JobSelectField<String>(
                                  fieldKey: const ValueKey('projects-selector'),
                                  label: 'Projects',
                                  value: projectsUiValue,
                                  helperText: projectsUiValue == 'not_needed'
                                      ? 'No project criteria required; practical work is still assessed across the resume.'
                                      : 'Define relevant practical-work criteria to evaluate.',
                                  items: const [
                                    DropdownMenuItem(
                                      value: 'not_needed',
                                      child: Text('Not needed'),
                                    ),
                                    DropdownMenuItem(
                                      value: 'optional',
                                      child: Text('Optional'),
                                    ),
                                    DropdownMenuItem(
                                      value: 'required',
                                      child: Text('Required'),
                                    ),
                                  ],
                                  onChanged: (value) {
                                    if (value == null) return;
                                    setState(() {
                                      _projectsRequirementController.text =
                                          switch (value) {
                                            'not_needed' => 'not_applicable',
                                            'optional' => 'preferred',
                                            _ => 'required',
                                          };
                                    });
                                  },
                                ),
                              ),
                              if (experienceUiValue != 'none')
                                JobFormField(
                                  controller: _experienceYearsController,
                                  label: 'Experience target (years)',
                                  hintText: 'e.g. 0.5',
                                  helperText:
                                      'Use a decimal for fractional years, such as 0.5 for six months.',
                                  keyboardType:
                                      const TextInputType.numberWithOptions(
                                        decimal: true,
                                      ),
                                  required: true,
                                  textInputAction: TextInputAction.next,
                                  validator: (value) {
                                    final years = double.tryParse(
                                      (value ?? '').trim(),
                                    );
                                    return years != null &&
                                            years.isFinite &&
                                            years > 0
                                        ? null
                                        : 'Enter a positive number of years.';
                                  },
                                ),
                              if (projectsUiValue != 'not_needed')
                                JobFormField(
                                  controller: _projectCriteriaController,
                                  label: 'Project criteria',
                                  hintText:
                                      'e.g. A mobile app with user authentication',
                                  helperText:
                                      'Describe the project evidence relevant to this role.',
                                  maxLines: 2,
                                  required: true,
                                  textInputAction: TextInputAction.next,
                                  onChanged: () => setState(() {}),
                                  validator: (value) =>
                                      _hasMeaningfulCriteria(value ?? '')
                                      ? null
                                      : 'Add specific project criteria.',
                                ),
                              const SizedBox(height: 4),
                              Theme(
                                data: Theme.of(
                                  context,
                                ).copyWith(dividerColor: Colors.transparent),
                                child: ExpansionTile(
                                  tilePadding: EdgeInsets.zero,
                                  childrenPadding: const EdgeInsets.only(
                                    bottom: 8,
                                  ),
                                  title: const Text(
                                    'Advanced scoring settings',
                                    style: TextStyle(
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                  subtitle: const Text(
                                    'Choose how skills and education affect scoring',
                                  ),
                                  children: [
                                    _ResponsiveFieldRow(
                                      first: _ScoringRequirementField(
                                        label: 'Skills scoring',
                                        value: _skillsRequirementController,
                                        options: const [
                                          'required',
                                          'preferred',
                                          'not_applicable',
                                        ],
                                        onSelectionChanged: () =>
                                            setState(() {}),
                                      ),
                                      second: _ScoringRequirementField(
                                        label: 'Education scoring',
                                        value: _educationRequirementController,
                                        options: const [
                                          'required',
                                          'preferred',
                                          'not_applicable',
                                        ],
                                        onSelectionChanged: () =>
                                            setState(() {}),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              _buildScoringPreview(),
                            ],
                          ),
                  ),
                  const SizedBox(height: 16),
                  _JobFormSection(
                    number: '03',
                    title: 'Job Description',
                    subtitle:
                        'Describe responsibilities, expectations, and what success looks like.',
                    icon: Icons.subject_rounded,
                    child: JobFormField(
                      controller: _descriptionController,
                      label: 'Description',
                      hintText:
                          'Outline the role’s responsibilities, key expectations, and the impact this person will make.',
                      helperText:
                          'A clear description helps candidates understand the opportunity.',
                      minLines: 5,
                      maxLines: 8,
                      required: true,
                      textInputAction: TextInputAction.newline,
                    ),
                  ),
                  const SizedBox(height: 20),
                  Align(
                    alignment: Alignment.centerRight,
                    child: FilledButton.icon(
                      onPressed: _saveJob,
                      icon: Icon(isEditing ? Icons.save_outlined : Icons.add),
                      label: Text(isEditing ? 'Save changes' : 'Publish job'),
                      style: FilledButton.styleFrom(
                        backgroundColor: const Color(0xFF2563EB),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 22,
                          vertical: 15,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 32),
                ],
              ),
            ),
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
    this.minLines,
    this.hintText,
    this.helperText,
    this.required = false,
    this.keyboardType,
    this.textInputAction,
    this.onChanged,
    this.validator,
  });

  final TextEditingController controller;
  final String label;
  final int maxLines;
  final int? minLines;
  final String? hintText;
  final String? helperText;
  final bool required;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final VoidCallback? onChanged;
  final FormFieldValidator<String>? validator;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        key: ValueKey('job-field-${label.toLowerCase()}'),
        controller: controller,
        maxLines: maxLines,
        minLines: minLines,
        keyboardType: keyboardType,
        textInputAction: textInputAction,
        onChanged: (_) => onChanged?.call(),
        validator:
            validator ??
            (required
                ? (value) => value == null || value.trim().isEmpty
                      ? 'Please enter ${label.toLowerCase()}.'
                      : null
                : null),
        autovalidateMode: AutovalidateMode.onUserInteraction,
        decoration: _jobFieldDecoration(
          label: required ? '$label *' : label,
          hintText: hintText,
          helperText: helperText,
        ),
      ),
    );
  }
}

InputDecoration _jobFieldDecoration({
  required String label,
  String? hintText,
  String? helperText,
}) {
  const borderColor = Color(0xFFD8E0EB);
  const focusColor = Color(0xFF2563EB);
  return InputDecoration(
    labelText: label,
    hintText: hintText,
    helperText: helperText,
    helperMaxLines: 2,
    isDense: true,
    filled: true,
    fillColor: const Color(0xFFFAFBFD),
    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(10),
      borderSide: const BorderSide(color: borderColor),
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(10),
      borderSide: const BorderSide(color: borderColor),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(10),
      borderSide: const BorderSide(color: focusColor, width: 1.5),
    ),
    errorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(10),
      borderSide: const BorderSide(color: Color(0xFFB91C1C)),
    ),
    focusedErrorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(10),
      borderSide: const BorderSide(color: Color(0xFFB91C1C), width: 1.5),
    ),
  );
}

class _ResponsiveFieldRow extends StatelessWidget {
  const _ResponsiveFieldRow({required this.first, required this.second});

  final Widget first;
  final Widget second;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < 640) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [first, second],
          );
        }
        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(child: first),
            const SizedBox(width: 16),
            Expanded(child: second),
          ],
        );
      },
    );
  }
}

class _JobFormSection extends StatelessWidget {
  const _JobFormSection({
    required this.number,
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.child,
  });

  final String number;
  final String title;
  final String subtitle;
  final IconData icon;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 2),
      padding: const EdgeInsets.fromLTRB(20, 18, 20, 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE2E8F0)),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF0F172A).withValues(alpha: 0.025),
            blurRadius: 12,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: const Color(0xFFEFF6FF),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, size: 20, color: const Color(0xFF2563EB)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '$number  $title',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF0F172A),
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: const TextStyle(
                        fontSize: 12,
                        height: 1.35,
                        color: Color(0xFF64748B),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          child,
        ],
      ),
    );
  }
}

class _LegacyPolicyNotice extends StatelessWidget {
  const _LegacyPolicyNotice();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFBEB),
        border: Border.all(color: const Color(0xFFFDE68A)),
        borderRadius: BorderRadius.circular(10),
      ),
      child: const Text(
        'This legacy posting keeps its original scoring behavior. Scoring settings are not migrated automatically.',
        style: TextStyle(color: Color(0xFF713F12), fontSize: 12),
      ),
    );
  }
}

class _JobSelectField<T> extends StatelessWidget {
  const _JobSelectField({
    this.fieldKey,
    required this.label,
    required this.value,
    required this.items,
    required this.onChanged,
    this.helperText,
  });

  final Key? fieldKey;
  final String label;
  final T value;
  final List<DropdownMenuItem<T>> items;
  final ValueChanged<T?> onChanged;
  final String? helperText;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: DropdownButtonFormField<T>(
        key: fieldKey,
        initialValue: value,
        isExpanded: true,
        menuMaxHeight: 360,
        items: items,
        onChanged: onChanged,
        decoration: _jobFieldDecoration(label: label, helperText: helperText),
      ),
    );
  }
}

class _ScoringRequirementField extends StatelessWidget {
  const _ScoringRequirementField({
    required this.label,
    required this.value,
    required this.options,
    required this.onSelectionChanged,
  });

  final String label;
  final TextEditingController value;
  final List<String> options;
  final VoidCallback onSelectionChanged;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: DropdownButtonFormField<String>(
        initialValue: options.contains(value.text) ? value.text : options.first,
        items: options
            .map(
              (option) => DropdownMenuItem(
                value: option,
                child: Text(switch (option) {
                  'required' => 'Required',
                  'preferred' => 'Preferred',
                  'not_applicable' => 'Not applicable',
                  _ => option,
                }),
              ),
            )
            .toList(),
        onChanged: (selection) {
          if (selection != null) {
            value.text = selection;
            onSelectionChanged();
          }
        },
        decoration: _jobFieldDecoration(label: label),
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
    this.showActionButton = true,
  });

  final String title;
  final String subtitle;
  final String actionLabel;
  final IconData actionIcon;
  final VoidCallback actionOnPressed;
  final List<Widget> children;
  final Widget? floatingActionButton;
  final bool showActionButton;

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
                if (showActionButton)
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
  const PillAction({
    super.key,
    required this.label,
    required this.onTap,
    this.danger = false,
  });

  final String label;
  final VoidCallback onTap;
  final bool danger;

  @override
  Widget build(BuildContext context) {
    final color = danger ? const Color(0xFFDC2626) : const Color(0xFF2563EB);
    return ActionChip(
      label: Text(label),
      onPressed: onTap,
      backgroundColor: color.withValues(alpha: 0.08),
      labelStyle: TextStyle(color: color, fontWeight: FontWeight.w700),
    );
  }
}
