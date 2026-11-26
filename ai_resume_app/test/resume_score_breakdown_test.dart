import 'package:ai_resume_app/screens/local_resume_store.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('reads version 3 practical work score and maximum', () {
    final breakdown = ResumeScoreBreakdown.fromMap({
      'skillsScore': 20,
      'skillsMax': 40,
      'experienceScore': 25,
      'experienceMax': 25,
      'educationScore': 20,
      'educationMax': 20,
      'practicalWorkScore': 14,
      'practicalWorkMax': 15,
      'finalScore': 79,
    });

    expect(breakdown.practicalWorkScore, 14);
    expect(breakdown.practicalWorkMax, 15);
  });

  test('falls back to legacy projects score fields', () {
    final breakdown = ResumeScoreBreakdown.fromMap({
      'projectsScore': 11.25,
      'projectsMax': 15,
      'finalScore': 80,
    });

    expect(breakdown.practicalWorkScore, 11.25);
    expect(breakdown.practicalWorkMax, 15);
  });
}
