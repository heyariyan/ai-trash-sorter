import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "raspberry-pi" / "app"))

from display.display import ConsoleDisplay, MockDisplay, SSD1306I2CDisplay, DisplayError  # noqa: E402


class MockLumaDevice:
    def __init__(self) -> None:
        self.displayed_images = []
        self.cleared = False

    def display(self, image) -> None:
        self.displayed_images.append(image)

    def clear(self) -> None:
        self.cleared = True


class DisplayTests(unittest.TestCase):
    def test_mock_display_records_all_events(self) -> None:
        display = MockDisplay()
        display.show_status("Ready")
        display.show_prediction("METAL", 0.95)
        display.show_bin_status("METAL", 15.5)
        display.show_feedback_prompt("METAL correct?", "PLASTIC")
        display.show_error("Home error")
        display.close()

        self.assertEqual(display.last_status, "Ready")
        self.assertEqual(display.last_prediction, ("METAL", 0.95))
        self.assertEqual(display.last_bin_status, ("METAL", 15.5))
        self.assertEqual(display.last_feedback, ("METAL correct?", "PLASTIC"))
        self.assertEqual(display.last_error, "Home error")

        action_names = [msg[0] for msg in display.messages]
        self.assertEqual(
            action_names,
            ["status", "prediction", "bin_status", "feedback", "error", "close"],
        )

    def test_console_display_runs_without_exceptions(self) -> None:
        display = ConsoleDisplay()
        display.show_status("Calibrating")
        display.show_prediction("BIODEGRADABLE", 0.88)
        display.show_bin_status("BIODEGRADABLE", 20.0)
        display.show_feedback_prompt("BIODEGRADABLE correct?")
        display.show_feedback_prompt("Select correct bin", "OTHER")
        display.show_error("Test warning")
        display.close()

    def test_ssd1306_draws_to_mock_device(self) -> None:
        device = MockLumaDevice()
        oled = SSD1306I2CDisplay(device=device, width=128, height=64)

        oled.show_status("Ready")
        oled.show_prediction("PLASTIC", 0.92)
        oled.show_bin_status("PLASTIC", 18.2)
        oled.show_feedback_prompt("PLASTIC correct?")
        oled.show_feedback_prompt("Select correct bin", "METAL")
        oled.show_error("Sensor timeout")
        oled.close()

        self.assertEqual(len(device.displayed_images), 6)
        self.assertTrue(device.cleared)
        for img in device.displayed_images:
            self.assertEqual(img.size, (128, 64))

    def test_ssd1306_start_raises_display_error_when_unavailable(self) -> None:
        oled = SSD1306I2CDisplay()
        # luma is not installed in standard test env, so start() must raise DisplayError
        with self.assertRaises(DisplayError):
            oled.start()


if __name__ == "__main__":
    unittest.main()
