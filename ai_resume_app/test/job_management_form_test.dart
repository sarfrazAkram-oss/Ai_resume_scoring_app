import 'package:ai_resume_app/screens/job_management_screen.dart';
import 'package:ai_resume_app/screens/local_resume_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _FormHarness extends StatefulWidget {
  const _FormHarness();

  @override
  State<_FormHarness> createState() => _FormHarnessState();
}

class _FormHarnessState extends State<_FormHarness> {
  JobItem? savedJob;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          ElevatedButton(
            onPressed: () async {
              final result = await Navigator.of(context).push<JobItem>(
                MaterialPageRoute(builder: (_) => const CreateJobScreen()),
              );
              setState(() => savedJob = result);
            },
            child: const Text('Open form'),
          ),
          if (savedJob != null)
            Text(
              'Saved: ${savedJob!.title}; '
              'experience=${savedJob!.experienceRequirement}; '
              'projects=${savedJob!.projectsRequirement}',
            ),
        ],
      ),
    );
  }
}

JobItem _existingJob() => const JobItem(
  id: 'job-1',
  title: 'Product Designer',
  department: 'Product',
  requiredSkills: 'Figma, Research',
  experience: '2 years',
  education: 'Design degree',
  description: 'Design product experiences.',
  location: 'Remote',
  employmentType: 'Full-time',
  salaryRange: '',
  applicants: 4,
  status: 'Open',
  jobType: 'experienced',
  skillsRequirement: 'preferred',
  experienceRequirement: 'required',
  experienceYears: '2',
  educationRequirement: 'required',
  projectsRequirement: 'preferred',
  projectCriteria: 'Product case study',
  scoringPolicyVersion: 2,
);

Finder _field(String label) =>
    find.byKey(ValueKey('job-field-${label.toLowerCase()}'));

Future<void> _enter(WidgetTester tester, String label, String value) async {
  final field = _field(label);
  await tester.ensureVisible(field);
  await tester.enterText(field, value);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('Create form is grouped and shows inline required validation', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1200, 1800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const MaterialApp(home: CreateJobScreen()));

    expect(find.textContaining('Basic Job Details'), findsOneWidget);
    expect(find.textContaining('Candidate Requirements'), findsOneWidget);
    expect(find.textContaining('Job Description'), findsOneWidget);
    expect(find.text('Number of Applicants'), findsNothing);
    expect(find.text('Required Experience'), findsNothing);
    expect(find.text('Scoring Breakdown'), findsOneWidget);

    final publish = find.text('Publish job');
    await tester.ensureVisible(publish);
    await tester.tap(publish);
    await tester.pumpAndSettle();

    expect(find.text('Please enter job title.'), findsOneWidget);
    expect(find.text('Please enter location.'), findsOneWidget);
    expect(find.text('Please enter description.'), findsOneWidget);
  });

  testWidgets('None experience maps to not applicable and publishes policy', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1200, 1800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const MaterialApp(home: _FormHarness()));
    await tester.tap(find.text('Open form'));
    await tester.pumpAndSettle();

    await _enter(tester, 'Job title', 'Flutter Developer');
    await _enter(tester, 'Location', 'Remote');
    await _enter(tester, 'Skills', 'Flutter, Dart');
    await _enter(tester, 'Education', 'Computer Science degree');
    await _enter(tester, 'Description', 'Build accessible mobile apps.');

    final experienceSelector = find.byKey(
      const ValueKey('experience-selector'),
    );
    await tester.ensureVisible(experienceSelector);
    await tester.tap(experienceSelector);
    await tester.pumpAndSettle();
    await tester.tap(find.text('None — No experience required').last);
    await tester.pumpAndSettle();
    expect(_field('Experience target (years)'), findsNothing);

    final projectsSelector = find.byKey(const ValueKey('projects-selector'));
    await tester.ensureVisible(projectsSelector);
    await tester.tap(projectsSelector);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Not needed').last);
    await tester.pumpAndSettle();
    expect(_field('Project criteria'), findsNothing);

    final publish = find.text('Publish job');
    await tester.ensureVisible(publish);
    await tester.tap(publish);
    await tester.pumpAndSettle();

    expect(
      find.text(
        'Saved: Flutter Developer; experience=not_applicable; '
        'projects=not_applicable',
      ),
      findsOneWidget,
    );
  });

  testWidgets('Edit form loads existing criteria and values', (tester) async {
    tester.view.physicalSize = const Size(1200, 1800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(home: CreateJobScreen(initialJob: _existingJob())),
    );

    expect(
      tester.widget<TextFormField>(_field('Job title')).controller!.text,
      'Product Designer',
    );
    expect(
      tester.widget<TextFormField>(_field('Skills')).controller!.text,
      'Figma, Research',
    );
    expect(
      tester
          .widget<TextFormField>(_field('Experience target (years)'))
          .controller!
          .text,
      '2',
    );
    expect(
      tester.widget<TextFormField>(_field('Project criteria')).controller!.text,
      'Product case study',
    );

    await tester.tap(find.text('Scoring Breakdown'));
    await tester.pumpAndSettle();
    expect(find.text('40 pts'), findsOneWidget);
    expect(find.text('25 pts'), findsOneWidget);
    expect(find.text('20 pts'), findsOneWidget);
    expect(find.text('15 pts (resume-wide evidence)'), findsOneWidget);
    expect(find.textContaining('Total possible: 100 points'), findsOneWidget);
  });
}
