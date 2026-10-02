import unittest

from app.services.education_scorer import score_education


class EducationScorerTests(unittest.TestCase):
    def test_completed_bscs_matches_bscs(self) -> None:
        result = score_education([{"text": "Completed BSCS"}], "BSCS")
        self.assertEqual(result["candidateDegree"], "BSCS")
        self.assertEqual(result["candidateLevel"], "bachelor")
        self.assertEqual(result["candidateField"], "computer_science")
        self.assertEqual(result["candidateStatus"], "completed")
        self.assertEqual(result["educationScore"], 20.0)

    def test_bsse_matches_explicit_bscs_or_bsse_alternatives(self) -> None:
        result = score_education([{"text": "BSSE"}], "BSCS or BSSE")
        self.assertEqual(result["requiredDegrees"], ["BSCS", "BSSE"])
        self.assertEqual(result["candidateDegree"], "BSSE")
        self.assertTrue(result["fieldMatched"])
        self.assertEqual(result["educationScore"], 20.0)

    def test_in_progress_bsse_receives_partial_credit(self) -> None:
        result = score_education(
            [{"text": "Software Engineering (BSSE), Superior University, 7th semester"}],
            "BSSE",
        )
        self.assertEqual(result["candidateLevel"], "bachelor")
        self.assertEqual(result["candidateField"], "software_engineering")
        self.assertEqual(result["candidateStatus"], "in_progress")
        self.assertEqual(result["educationScore"], 15.0)
        self.assertEqual(result["status"], "scored_in_progress")

    def test_future_dated_study_is_in_progress_with_credential_context(self) -> None:
        result = score_education([{"text": "BSSE 2023-2027"}], "BSSE")
        self.assertEqual(result["candidateStatus"], "in_progress")
        self.assertEqual(result["educationScore"], 15.0)

    def test_mbbs_matches_mbbs(self) -> None:
        result = score_education([{"text": "MBBS, completed"}], "MBBS required")
        self.assertEqual(result["candidateLevel"], "professional")
        self.assertEqual(result["candidateField"], "medicine")
        self.assertTrue(result["fieldMatched"])
        self.assertEqual(result["educationScore"], 20.0)

    def test_mbbs_does_not_match_bscs(self) -> None:
        result = score_education([{"text": "MBBS"}], "BSCS")
        self.assertFalse(result["fieldMatched"])
        self.assertEqual(result["educationScore"], 0.0)

    def test_bscs_does_not_match_mbbs(self) -> None:
        result = score_education([{"text": "BSCS"}], "MBBS")
        self.assertFalse(result["fieldMatched"])
        self.assertEqual(result["educationScore"], 0.0)

    def test_bds_matches_bds(self) -> None:
        result = score_education([{"text": "BDS"}], "BDS")
        self.assertEqual(result["candidateField"], "dentistry")
        self.assertEqual(result["educationScore"], 20.0)

    def test_pharm_d_matches_pharmacy_credential(self) -> None:
        result = score_education([{"text": "Pharm D"}], "Pharm-D")
        self.assertEqual(result["candidateDegree"], "Pharm-D")
        self.assertEqual(result["candidateField"], "pharmacy")
        self.assertEqual(result["educationScore"], 20.0)

    def test_bba_and_mba_match_business_degrees(self) -> None:
        bba = score_education([{"text": "BBA"}], "BBA")
        mba = score_education([{"text": "MBA"}], "MBA")
        self.assertEqual(bba["candidateField"], "business")
        self.assertEqual(mba["candidateField"], "business")
        self.assertEqual(bba["educationScore"], 20.0)
        self.assertEqual(mba["educationScore"], 20.0)

    def test_llb_matches_law_degree(self) -> None:
        result = score_education([{"text": "LL.B."}], "LLB")
        self.assertEqual(result["candidateField"], "law")
        self.assertEqual(result["educationScore"], 20.0)

    def test_generic_bachelor_matches_generic_bachelor(self) -> None:
        result = score_education(
            [{"text": "Completed Bachelor's degree"}], "Bachelor's degree"
        )
        self.assertEqual(result["candidateLevel"], "bachelor")
        self.assertEqual(result["candidateStatus"], "completed")
        self.assertEqual(result["educationScore"], 20.0)

    def test_master_meets_generic_bachelor_requirement(self) -> None:
        result = score_education([{"text": "MBA"}], "Bachelor's degree")
        self.assertEqual(result["educationScore"], 20.0)

    def test_fsc_is_one_level_below_bachelor(self) -> None:
        result = score_education([{"text": "FSC"}], "Bachelor's degree")
        self.assertEqual(result["candidateLevel"], "higher_secondary")
        self.assertEqual(result["educationScore"], 10.0)

    def test_missing_candidate_education_scores_zero(self) -> None:
        result = score_education([], "BSCS")
        self.assertIsNone(result["candidateDegree"])
        self.assertEqual(result["candidateStatus"], "unknown")
        self.assertEqual(result["educationScore"], 0.0)
        self.assertEqual(result["matchPercentage"], 0.0)

    def test_empty_and_unparseable_requirements_are_not_scored(self) -> None:
        for requirement in ("", "Relevant bachelor's degree"):
            with self.subTest(requirement=requirement):
                result = score_education([{"text": "BSCS"}], requirement)
                self.assertIsNone(result["educationScore"])
                self.assertIsNone(result["matchPercentage"])
                self.assertEqual(
                    result["status"], "not_scored_no_parseable_requirement"
                )

    def test_field_specific_bachelor_requires_level_and_field(self) -> None:
        match = score_education(
            [{"text": "BSCS"}], "Bachelor's degree in Computer Science"
        )
        unrelated = score_education(
            [{"text": "Completed MBBS"}], "Bachelor's degree in Computer Science"
        )
        in_progress = score_education(
            [{"text": "BSCS, 7th semester"}],
            "Bachelor's degree in Computer Science",
        )
        self.assertEqual(match["educationScore"], 20.0)
        self.assertEqual(unrelated["educationScore"], 0.0)
        self.assertEqual(in_progress["educationScore"], 15.0)

    def test_word_boundaries_prevent_ba_from_matching_bba(self) -> None:
        result = score_education([{"text": "BBA"}], "BA")
        self.assertFalse(result["fieldMatched"])
        self.assertEqual(result["educationScore"], 0.0)

    def test_unrelated_higher_professional_qualification_gets_no_field_credit(self) -> None:
        result = score_education([{"text": "MBBS"}], "Master's degree in Computer Science")
        self.assertFalse(result["fieldMatched"])
        self.assertEqual(result["educationScore"], 0.0)


if __name__ == "__main__":
    unittest.main()