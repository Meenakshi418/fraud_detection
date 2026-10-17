"""Offline tests for backend risk rules."""

import unittest

from backend.risk_analysis import analyze_risk


class AnalyzeRiskTests(unittest.TestCase):
    def test_empty_input_is_inconclusive(self):
        for value in ("", "   ", "...", None, 42, b"transcript"):
            with self.subTest(value=value):
                result = analyze_risk(value)
                self.assertEqual(result["risk_level"], "Inconclusive")
                self.assertIsNone(result["risk_score"])
                self.assertTrue(result["limitations"])

    def test_harmless_text_is_low(self):
        result = analyze_risk("The weather is sunny and the meeting starts at noon.")
        self.assertEqual(result["risk_level"], "Low")
        self.assertEqual(result["risk_score"], 0)
        self.assertEqual(result["reasons"], [])

    def test_money_or_bank_mention_alone_is_low(self):
        for text in (
            "I deposited money at the bank.",
            "The bank called about my account.",
            "Our training discusses passwords and AnyDesk software.",
        ):
            with self.subTest(text=text):
                result = analyze_risk(text)
                self.assertEqual(result["risk_level"], "Low")
                self.assertEqual(result["risk_score"], 0)

    def test_urgent_secret_transfer_is_high(self):
        result = analyze_risk(
            "Urgently transfer the funds right now and keep this secret from everyone."
        )
        self.assertEqual(result["risk_level"], "High")
        self.assertIn("Urgent request to transfer or send money", result["reasons"])
        self.assertIn("Secrecy request or threat/pressure", result["reasons"])

    def test_otp_or_password_request_is_high(self):
        for text in ("Please send me the OTP.", "Tell me your password now."):
            with self.subTest(text=text):
                result = analyze_risk(text)
                self.assertEqual(result["risk_level"], "High")
                self.assertIn("Request for a password, PIN, OTP, or verification code", result["reasons"])

    def test_payment_detail_change_is_medium(self):
        result = analyze_risk("Please update the bank account details for the next payment.")
        self.assertEqual(result["risk_level"], "Medium")
        self.assertIn("Request to change or use new payment or bank details", result["reasons"])

    def test_output_is_stable_and_has_documented_shape(self):
        text = "Skip verification and install AnyDesk to help me."
        first = analyze_risk(text)
        second = analyze_risk(text)
        self.assertEqual(first, second)
        self.assertEqual(
            set(first), {"risk_level", "risk_score", "reasons", "limitations"}
        )
        self.assertEqual(first["risk_level"], "High")

    def test_scores_stay_in_bounds(self):
        all_flags = (
            "Urgently transfer money to a new bank account, send me your OTP, "
            "I am your bank manager, skip verification, keep this secret, "
            "or your account will be closed, and install TeamViewer."
        )
        score = analyze_risk(all_flags)["risk_score"]
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        self.assertEqual(score, 100)


if __name__ == "__main__":
    unittest.main()
