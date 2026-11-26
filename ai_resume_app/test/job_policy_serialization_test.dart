import 'package:flutter_test/flutter_test.dart';
import 'package:ai_resume_app/screens/local_resume_store.dart';

JobItem _job({
  String title = 'Developer',
  int? policyVersion = 2,
  String jobType = 'experienced',
  String requiredSkills = 'Python, Flutter',
  String experience = '2 years',
  String education = 'BSCS',
  String skillsRequirement = 'required',
  String experienceRequirement = 'required',
  String experienceYears = '2.5',
  String educationRequirement = 'preferred',
  String projectsRequirement = 'required',
  String projectCriteria = 'Mobile application',
}) {
  return JobItem(
    id: 'job-1',
    title: title,
    department: 'Engineering',
    requiredSkills: requiredSkills,
    experience: experience,
    education: education,
    description: 'Build software',
    location: 'Remote',
    employmentType: 'Full time',
    salaryRange: '',
    applicants: 0,
    status: 'Open',
    jobType: jobType,
    skillsRequirement: skillsRequirement,
    experienceRequirement: experienceRequirement,
    experienceYears: experienceYears,
    educationRequirement: educationRequirement,
    projectsRequirement: projectsRequirement,
    projectCriteria: projectCriteria,
    scoringPolicyVersion: policyVersion,
  );
}

void main() {
  test('Create serialization includes complete version two policy', () {
    final data = _job().toFirestore(createdBy: 'recruiter-1');

    expect(data['scoringPolicyVersion'], 2);
    expect(data['jobType'], 'experienced');
    expect(data['skillsRequirement'], 'required');
    expect(data['experienceRequirement'], 'required');
    expect(data['experienceYears'], '2.5');
    expect(data['educationRequirement'], 'preferred');
    expect(data['projectsRequirement'], 'required');
    expect(data['projectCriteria'], 'Mobile application');
    expect(data['requiredSkills'], 'Python, Flutter');
    expect(data['requiredEducation'], 'BSCS');
  });

  test('Edit serialization retains policy while updating ordinary fields', () {
    final data = _job(
      title: 'Senior Developer',
    ).toFirestore(createdBy: 'recruiter-1');

    expect(data['title'], 'Senior Developer');
    expect(data['scoringPolicyVersion'], 2);
    expect(data['experienceYears'], '2.5');
    expect(data['projectCriteria'], 'Mobile application');
  });

  test(
    'Legacy edit serialization does not silently migrate policy version',
    () {
      final data = _job(
        policyVersion: null,
      ).toFirestore(createdBy: 'recruiter-1');

      expect(data.containsKey('scoringPolicyVersion'), isFalse);
      expect(data.containsKey('skillsRequirement'), isFalse);
      expect(data.containsKey('projectCriteria'), isFalse);
    },
  );

  test(
    'Scoring policy comparison distinguishes scoring from ordinary edits',
    () {
      final original = _job();
      expect(original.hasSameScoringPolicyAs(_job(title: 'New title')), isTrue);

      final scoringEdits = [
        _job(policyVersion: 1),
        _job(jobType: 'internship'),
        _job(requiredSkills: 'Dart'),
        _job(experience: '3 years'),
        _job(education: 'MSCS'),
        _job(skillsRequirement: 'preferred'),
        _job(experienceRequirement: 'preferred'),
        _job(experienceYears: '3'),
        _job(educationRequirement: 'required'),
        _job(projectsRequirement: 'preferred'),
        _job(projectCriteria: 'Web application'),
      ];

      for (final edited in scoringEdits) {
        expect(original.hasSameScoringPolicyAs(edited), isFalse);
      }
    },
  );
}
