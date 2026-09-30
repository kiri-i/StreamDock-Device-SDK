"""N4 decoder regression tests; no USB device or native transport is required.

From Python-SDK, after installing Pillow:
    PYTHONPATH=src python -m unittest discover -s tests -v
"""

import sys
import types
import unittest
from unittest.mock import patch

# Import the actual SDK decoder and event types without loading the native
# transport library. Transport behavior is outside these decoder unit tests.
transport_name = "StreamDock.Transport.LibUSBHIDAPI"
transport_stub = types.ModuleType(transport_name)
transport_stub.LibUSBHIDAPI = object
with patch.dict(sys.modules, {transport_name: transport_stub}):
    from StreamDock.Devices.StreamDockN4 import StreamDockN4
    from StreamDock.InputTypes import ButtonKey, Direction, EventType, InputEvent, KnobId


class DecoderOnlyN4(StreamDockN4):
    """Skip hardware initialization and cleanup; use the real inherited decoder."""

    def __init__(self):
        pass

    def __del__(self):
        pass


# Expectations are deliberately independent of the implementation's maps.
ROTATIONS = (
    (0xA0, KnobId.KNOB_1, Direction.LEFT),
    (0xA1, KnobId.KNOB_1, Direction.RIGHT),
    (0x50, KnobId.KNOB_2, Direction.LEFT),
    (0x51, KnobId.KNOB_2, Direction.RIGHT),
    (0x90, KnobId.KNOB_3, Direction.LEFT),
    (0x91, KnobId.KNOB_3, Direction.RIGHT),
    (0x70, KnobId.KNOB_4, Direction.LEFT),
    (0x71, KnobId.KNOB_4, Direction.RIGHT),
)
PRESSES = (
    (0x37, KnobId.KNOB_1),
    (0x35, KnobId.KNOB_2),
    (0x33, KnobId.KNOB_3),
    (0x36, KnobId.KNOB_4),
)
BUTTONS = (
    (11, ButtonKey.KEY_1), (12, ButtonKey.KEY_2),
    (13, ButtonKey.KEY_3), (14, ButtonKey.KEY_4),
    (15, ButtonKey.KEY_5), (6, ButtonKey.KEY_6),
    (7, ButtonKey.KEY_7), (8, ButtonKey.KEY_8),
    (9, ButtonKey.KEY_9), (10, ButtonKey.KEY_10),
    (1, ButtonKey.KEY_11), (2, ButtonKey.KEY_12),
    (3, ButtonKey.KEY_13), (4, ButtonKey.KEY_14),
)


class N4InputTests(unittest.TestCase):
    def setUp(self):
        self.device = DecoderOnlyN4()

    def test_all_eight_rotation_codes(self):
        for code, knob, direction in ROTATIONS:
            with self.subTest(code=hex(code)):
                self.assertEqual(
                    self.device.decode_input_event(code, 0x00),
                    InputEvent(EventType.KNOB_ROTATE, knob_id=knob, direction=direction),
                )

    def test_rotation_rejects_non_rotation_states(self):
        for code, _, _ in ROTATIONS:
            for state in (0x01, 0x02, 0xFF):
                with self.subTest(code=hex(code), state=state):
                    self.assertEqual(
                        self.device.decode_input_event(code, state),
                        InputEvent(EventType.UNKNOWN),
                    )

    def test_all_four_press_codes_use_observed_state_one(self):
        for code, knob in PRESSES:
            with self.subTest(code=hex(code)):
                self.assertEqual(
                    self.device.decode_input_event(code, 0x01),
                    InputEvent(EventType.KNOB_PRESS, knob_id=knob, state=1),
                )

    def test_press_rejects_zero_release_and_unknown_states(self):
        for code, _ in PRESSES:
            for state in (0x00, 0x02, 0xFF):
                with self.subTest(code=hex(code), state=state):
                    self.assertEqual(
                        self.device.decode_input_event(code, state),
                        InputEvent(EventType.UNKNOWN),
                    )

    def test_existing_button_mapping_and_state_normalization(self):
        for code, key in BUTTONS:
            for raw_state, expected_state in ((0x01, 1), (0x00, 0), (0x02, 0)):
                with self.subTest(code=code, state=raw_state):
                    self.assertEqual(
                        self.device.decode_input_event(code, raw_state),
                        InputEvent(EventType.BUTTON, key=key, state=expected_state),
                    )

    def test_unknown_codes_remain_unknown(self):
        for code in (0x00, 0x05, 0x38, 0x39, 0x40, 0x43, 0xFF):
            for state in (0x00, 0x01, 0x02):
                with self.subTest(code=hex(code), state=state):
                    self.assertEqual(
                        self.device.decode_input_event(code, state),
                        InputEvent(EventType.UNKNOWN),
                    )


if __name__ == "__main__":
    unittest.main()
