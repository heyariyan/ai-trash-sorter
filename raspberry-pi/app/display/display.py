"""Status-display contract with rich console and SSD1306 OLED adapters."""

from __future__ import annotations

from typing import Protocol


class DisplayError(RuntimeError):
    """Raised when a display adapter cannot be started or updated."""


class Display(Protocol):
    def show_status(self, message: str) -> None:
        """Show a machine status message."""

    def show_prediction(self, category: str, confidence: float) -> None:
        """Show the latest AI prediction with confidence."""

    def show_feedback_prompt(self, message: str, selected_label: str | None = None) -> None:
        """Show a feedback prompt and optional selected correction label."""

    def show_bin_status(self, category: str, distance_cm: float | None) -> None:
        """Show post-drop bin distance measurement."""

    def show_error(self, message: str) -> None:
        """Show an error message."""

    def close(self) -> None:
        """Release display resources."""


class ConsoleDisplay:
    """Rich console display implementation for SSH and development runs."""

    def show_status(self, message: str) -> None:
        print(f"[STATUS] {message}", flush=True)

    def show_prediction(self, category: str, confidence: float) -> None:
        pct = confidence * 100
        bars = int(pct // 10)
        meter = "#" * bars + "-" * (10 - bars)
        print(f"[PREDICTION] {category} ({pct:.1f}%) [{meter}]", flush=True)

    def show_feedback_prompt(self, message: str, selected_label: str | None = None) -> None:
        if selected_label:
            print(f"[FEEDBACK] {message} -> > [ {selected_label} ] < (PREV/NEXT -> YES)", flush=True)
        else:
            print(f"[FEEDBACK] {message} [YES: GPIO20 / NO: GPIO21]", flush=True)

    def show_bin_status(self, category: str, distance_cm: float | None) -> None:
        dist_str = f"{distance_cm:.1f} cm" if distance_cm is not None else "N/A"
        print(f"[BIN STATUS] Bin: {category} | Level: {dist_str}", flush=True)

    def show_error(self, message: str) -> None:
        print(f"[ERROR] {message}", flush=True)

    def close(self) -> None:
        return


class MockDisplay:
    """Record display calls and latest state for tests."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []
        self.last_status: str | None = None
        self.last_prediction: tuple[str, float] | None = None
        self.last_feedback: tuple[str, str | None] | None = None
        self.last_bin_status: tuple[str, float | None] | None = None
        self.last_error: str | None = None

    def show_status(self, message: str) -> None:
        self.last_status = message
        self.messages.append(("status", message))

    def show_prediction(self, category: str, confidence: float) -> None:
        self.last_prediction = (category, confidence)
        self.messages.append(("prediction", f"{category}:{confidence:.6f}"))

    def show_feedback_prompt(self, message: str, selected_label: str | None = None) -> None:
        self.last_feedback = (message, selected_label)
        suffix = f":{selected_label}" if selected_label else ""
        self.messages.append(("feedback", f"{message}{suffix}"))

    def show_bin_status(self, category: str, distance_cm: float | None) -> None:
        self.last_bin_status = (category, distance_cm)
        dist_str = f"{distance_cm:.1f}" if distance_cm is not None else "None"
        self.messages.append(("bin_status", f"{category}:{dist_str}"))

    def show_error(self, message: str) -> None:
        self.last_error = message
        self.messages.append(("error", message))

    def close(self) -> None:
        self.messages.append(("close", ""))


class SSD1306I2CDisplay:
    """Rich SSD1306 OLED adapter for 128x64 / 128x32 I2C GPIO2/GPIO3 modules.

    Uses Pillow drawing primitives for clean typography, headers, boxes,
    progress meters, and interactive selection indicators.
    """

    def __init__(
        self,
        *,
        port: int = 1,
        address: int = 0x3C,
        width: int = 128,
        height: int = 64,
        device=None,
    ) -> None:
        self.port = port
        self.address = address
        self.width = width
        self.height = height
        self._device = device
        self._canvas = None

    def start(self) -> None:
        if self._device is not None:
            return
        try:
            from luma.core.interface.serial import i2c
            from luma.core.render import canvas
            from luma.oled.device import ssd1306

            serial = i2c(port=self.port, address=self.address)
            self._device = ssd1306(serial, width=self.width, height=self.height)
            self._canvas = canvas
        except Exception as exc:
            raise DisplayError(
                "SSD1306 OLED dependencies or I2C device are unavailable"
            ) from exc

    def _draw_screen(self, draw_fn) -> None:
        if self._device is None:
            self.start()
        if self._canvas is not None:
            with self._canvas(self._device) as draw:
                draw_fn(draw)
        else:
            from PIL import Image, ImageDraw

            img = Image.new("1", (self.width, self.height), 0)
            draw = ImageDraw.Draw(img)
            draw_fn(draw)
            if hasattr(self._device, "display"):
                self._device.display(img)

    def _draw_header(self, draw, title: str) -> None:
        draw.rectangle((0, 0, self.width - 1, 12), fill=1)
        draw.text((3, 1), title[:22].upper(), fill=0)

    def show_status(self, message: str) -> None:
        def draw_ui(draw):
            self._draw_header(draw, "AI TRASH SORTER")
            draw.rectangle((4, 18, self.width - 5, 46), outline=1)
            draw.text((10, 24), message[:18], fill=1)
            draw.text((10, 50), "Ready / Standby", fill=1)

        self._draw_screen(draw_ui)

    def show_prediction(self, category: str, confidence: float) -> None:
        def draw_ui(draw):
            self._draw_header(draw, "AI PREDICTION")
            cat_text = category.upper()
            draw.text((12, 16), cat_text, fill=1)

            pct = max(0.0, min(1.0, confidence)) * 100
            draw.text((12, 30), f"Conf: {pct:.1f}%", fill=1)

            bar_x0, bar_y0, bar_x1, bar_y1 = 10, 46, self.width - 11, 58
            draw.rectangle((bar_x0, bar_y0, bar_x1, bar_y1), outline=1)
            fill_width = int((bar_x1 - bar_x0 - 2) * max(0.0, min(1.0, confidence)))
            if fill_width > 0:
                draw.rectangle((bar_x0 + 1, bar_y0 + 1, bar_x0 + 1 + fill_width, bar_y1 - 1), fill=1)

        self._draw_screen(draw_ui)

    def show_feedback_prompt(self, message: str, selected_label: str | None = None) -> None:
        def draw_ui(draw):
            if selected_label:
                self._draw_header(draw, "CORRECTION")
                draw.text((4, 15), "Select Correct Bin:", fill=1)
                draw.rectangle((6, 28, self.width - 7, 44), fill=1)
                draw.text((14, 31), f"> {selected_label} <", fill=0)
                draw.text((4, 49), "PREV/NEXT  YES:Save", fill=1)
            else:
                self._draw_header(draw, "USER FEEDBACK")
                draw.text((6, 16), message[:20], fill=1)
                draw.rectangle((6, 32, 56, 50), outline=1)
                draw.text((12, 36), "YES [1]", fill=1)
                draw.rectangle((66, 32, 116, 50), outline=1)
                draw.text((74, 36), "NO [2]", fill=1)

        self._draw_screen(draw_ui)

    def show_bin_status(self, category: str, distance_cm: float | None) -> None:
        def draw_ui(draw):
            self._draw_header(draw, "BIN STATUS")
            draw.text((6, 16), f"Bin: {category}", fill=1)
            dist_str = f"{distance_cm:.1f} cm" if distance_cm is not None else "Timeout"
            draw.text((6, 32), f"Dist: {dist_str}", fill=1)
            draw.text((6, 48), "Post-drop sample OK", fill=1)

        self._draw_screen(draw_ui)

    def show_error(self, message: str) -> None:
        def draw_ui(draw):
            draw.rectangle((0, 0, self.width - 1, 13), fill=1)
            draw.text((3, 1), "! SYSTEM ERROR !", fill=0)
            draw.text((4, 18), message[:20], fill=1)
            if len(message) > 20:
                draw.text((4, 30), message[20:40], fill=1)
            draw.rectangle((4, 46, self.width - 5, 60), outline=1)
            draw.text((10, 48), "SAFE STOP ENGAGED", fill=1)

        self._draw_screen(draw_ui)

    def close(self) -> None:
        if self._device is not None:
            try:
                if hasattr(self._device, "clear"):
                    self._device.clear()
            except Exception:
                pass
            self._device = None
            self._canvas = None
