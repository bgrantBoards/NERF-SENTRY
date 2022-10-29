import usb_cdc
import asyncio
from sentry import PanTiltCmd, SpinCmd, FireCmd, SafetyCmd


class SerialParser:
    """
    Class that handles all serial communication with the Raspi host.
    Raspi will send motor commands to the pico, this class will handle
    recieving and parsing those commands.
    """

    def __init__(self) -> None:
        # define serial protocol command names
        self.commands = {
            "SET":   ["PAN", "TILT"],
            "SPIN":   ["UP", "DOWN"],
            "SAFETY": ["ON", "OFF"],
            "FIRE":   []
        }

        # setup serial connection
        self.cmd_serial = usb_cdc.data

        self.key_states = {
            "w": False,
            "a": False,
            "s": False,
            "d": False,
            "f": False,
            "j": False,
        }

    async def parse_commands(self):
        """
        Listens for new lines coming in from the serial connection
        """
        while True:
            await asyncio.sleep(0)
            available = self.cmd_serial.in_waiting
            if available:
                line = self.cmd_serial.readline()[:-1]
                print(line.decode("utf-8"))

    def get_op_control_cmds(self):
        """
        Listens for operator keyboard controls from the host serial connection and returns command messages.
        """
        test_speed = 0.1

        # only get lines from serial if there are new lines to get
        available = self.cmd_serial.in_waiting
        if available:
            # get a line and begin parsing
            # key press data comes in from op control line by line in this format: "{'j', 'a', 'g', 'h'}"
            pressed_keys = self.cmd_serial.readline()[:-1].decode("utf-8").split("'")

            # pop out characters that we don't want to consider
            for idx, c in enumerate(pressed_keys):
                if not c.islower():
                    pressed_keys.pop(idx)
            # switch on characters to get commands
            commands = []
            if "w" in pressed_keys and not "s" in pressed_keys:
                self.key_states["w"] = True
                commands.append(PanTiltCmd("tilt", test_speed))
            elif self.key_states["w"]: # if the key was unpressed
                self.key_states["w"] = False
                commands.append(PanTiltCmd("tilt", 0))

            if "a" in pressed_keys and not "d" in pressed_keys:
                commands.append(PanTiltCmd("pan", -test_speed))
                self.key_states["a"] = True
            elif self.key_states["a"]: # if the key was unpressed
                self.key_states["a"] = False
                commands.append(PanTiltCmd("pan", 0))

            if "s" in pressed_keys and not "w" in pressed_keys:
                commands.append(PanTiltCmd("tilt", -test_speed))
                self.key_states["s"] = True
            elif self.key_states["s"]: # if the key was unpressed
                self.key_states["s"] = False
                commands.append(PanTiltCmd("tilt", 0))

            if "d" in pressed_keys and not "a" in pressed_keys:
                commands.append(PanTiltCmd("pan", test_speed))
                self.key_states["d"] = True
            elif self.key_states["d"]: # if the key was unpressed
                self.key_states["d"] = False
                commands.append(PanTiltCmd("pan", 0))

            if "f" in pressed_keys:
                commands.append(FireCmd())
                self.key_states["f"] = True

            # if "j" in pressed_keys:
            #     commands.append(SpinCmd())
            #     self.key_states["j"] = True

            return commands

