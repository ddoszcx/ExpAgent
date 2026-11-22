import json
import unittest

from harness.tool_registry import execute_tool


class TestSrm(unittest.TestCase):
    def test_agent_can_serialize_srm_result(self):
        cases = [
            ({"n_control": 10000, "n_treatment": 9950}, "SRM_OK"),
            ({"n_control": 10000, "n_treatment": 8700}, "SRM_BROKEN"),
            ({"n_control": 8000, "n_treatment": 2000, "expected_ratio": 0.8}, "SRM_OK"),
        ]
        for arguments, expected_verdict in cases:
            with self.subTest(arguments=arguments):
                result = execute_tool("srm_check", json.dumps(arguments))
                payload = json.loads(json.dumps(result, allow_nan=False))
                self.assertEqual(payload["verdict"], expected_verdict)
                self.assertIs(payload["is_srm"], expected_verdict == "SRM_BROKEN")

    def test_reference_chi_square(self):
        # Expected counts are 50 and 50. Each group contributes 10**2 / 50.
        result = execute_tool("srm_check", {"n_control": 60, "n_treatment": 40})
        self.assertEqual(result["chi2_statistic"], 4.0)
        self.assertAlmostEqual(result["p_value"], 0.0455002639)
        self.assertEqual(result["verdict"], "SRM_OK")

    def test_invalid_inputs_return_error(self):
        for control, treatment, ratio in [(0, 0, 0.5), (-1, 100, 0.5), (50, 50, 1.0)]:
            with self.subTest(control=control, treatment=treatment, ratio=ratio):
                result = execute_tool("srm_check", {
                    "n_control": control, "n_treatment": treatment, "expected_ratio": ratio,
                })
                self.assertIn("error", result)
