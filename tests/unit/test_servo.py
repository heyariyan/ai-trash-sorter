import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "raspberry-pi" / "app"))

from motors.servo import GateConfig, MockServo, ServoGate  # noqa: E402


class ServoTests(unittest.TestCase):
    def test_gate_open_close_uses_configured_angles(self) -> None:
        servo = MockServo()
        servo.start()
        gate = ServoGate(servo, GateConfig(closed_angle=15, open_angle=105, settle_seconds=0))
        gate.open()
        self.assertTrue(gate.is_open)
        gate.close()
        self.assertFalse(gate.is_open)
        self.assertEqual(servo.positions, [105, 15])

    def test_gate_config_rejects_invalid_angle(self) -> None:
        with self.assertRaises(ValueError):
            GateConfig(open_angle=181)

    def test_mock_requires_start(self) -> None:
        with self.assertRaises(RuntimeError):
            MockServo().set_angle(90)


if __name__ == "__main__":
    unittest.main()
