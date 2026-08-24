import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "raspberry-pi" / "app"))

from object_detection import ObjectPresenceDetector  # noqa: E402
from sensors import MockUltrasonicSensor  # noqa: E402


class ObjectPresenceTests(unittest.TestCase):
    def test_present_and_clear_are_debounced(self) -> None:
        sensor = MockUltrasonicSensor([40.0, 10.0, 11.0, 35.0, 36.0])
        detector = ObjectPresenceDetector(sensor, present_threshold_cm=20.0)
        readings = [detector.poll() for _ in range(5)]
        self.assertFalse(readings[0].present)
        self.assertTrue(readings[2].present)
        self.assertTrue(readings[2].changed)
        self.assertFalse(readings[4].present)
        self.assertTrue(readings[4].changed)

    def test_invalid_read_does_not_change_state(self) -> None:
        sensor = MockUltrasonicSensor([10.0, None, float("nan")])
        detector = ObjectPresenceDetector(sensor, present_threshold_cm=20.0, present_samples=1)
        first = detector.poll()
        invalid_timeout = detector.poll()
        invalid_nan = detector.poll()
        self.assertTrue(first.present)
        self.assertTrue(first.valid)
        self.assertFalse(invalid_timeout.valid)
        self.assertTrue(invalid_timeout.present)
        self.assertFalse(invalid_nan.valid)
        self.assertTrue(invalid_nan.present)

    def test_configuration_rejects_invalid_threshold(self) -> None:
        with self.assertRaises(ValueError):
            ObjectPresenceDetector(MockUltrasonicSensor(), present_threshold_cm=0)


if __name__ == "__main__":
    unittest.main()
