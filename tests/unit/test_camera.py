import tempfile
import unittest
from pathlib import Path
import sys


APP_ROOT = Path(__file__).resolve().parents[2] / "raspberry-pi" / "app"
sys.path.insert(0, str(APP_ROOT))

from camera import CameraError, MockCamera  # noqa: E402


class MockCameraTests(unittest.TestCase):
    def test_capture_requires_start(self) -> None:
        camera = MockCamera()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(CameraError):
                camera.capture(Path(directory) / "frame.jpg")

    def test_capture_writes_frame_and_metadata(self) -> None:
        camera = MockCamera(width=320, height=240)
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "nested" / "frame.jpg"
            camera.start()
            result = camera.capture(destination)
            self.assertTrue(destination.exists())
            self.assertIn(b"SIMULATED_IMAGE", destination.read_bytes())
            camera.stop()

        self.assertEqual(result.path, destination)
        self.assertEqual(result.width, 320)
        self.assertEqual(result.height, 240)
        self.assertGreaterEqual(result.capture_time_ms, 0)
        self.assertTrue(result.simulated)
        self.assertEqual(camera.capture_count, 1)

    def test_start_and_stop_are_idempotent(self) -> None:
        camera = MockCamera()
        camera.start()
        camera.start()
        camera.stop()
        camera.stop()
        self.assertFalse(camera.started)


if __name__ == "__main__":
    unittest.main()
