import usb_cdc
import asyncio
from sentry import SpinCmd, FireCmd, SafetyCmd, PanTiltCmd
from actuators import Display


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

    def get_line(self):
        """
        Get a line from the serial connection
        """
        return self.cmd_serial.readline()[:-1].decode("utf-8")
    
    def get_op_control_cmds(self):
        """
        Listens for operator keyboard controls from the host serial connection and returns command messages.
        """
        pan_speed = 1
        tilt_speed = .3

        # only get lines from serial if there are new lines to get
        available = self.cmd_serial.in_waiting
        if available:
            # get a line and begin parsing
            # key press data comes in from op control line by line in this format: "{'j', 'a', 'g', 'h'}"
            pressed_keys = self.get_line().split("'")

            # pop out characters that we don't want to consider
            for idx, c in enumerate(pressed_keys):
                if not c.islower():
                    pressed_keys.pop(idx)
            # switch on characters to get commands
            commands = []
            if "w" in pressed_keys and not "s" in pressed_keys:
                self.key_states["w"] = True
                commands.append(PanTiltCmd("tilt", tilt_speed))
            elif self.key_states["w"]: # if the key was unpressed
                self.key_states["w"] = False
                commands.append(PanTiltCmd("tilt", 0))

            if "a" in pressed_keys and not "d" in pressed_keys:
                commands.append(PanTiltCmd("pan", -pan_speed))
                self.key_states["a"] = True
            elif self.key_states["a"]: # if the key was unpressed
                self.key_states["a"] = False
                commands.append(PanTiltCmd("pan", 0))

            if "s" in pressed_keys and not "w" in pressed_keys:
                commands.append(PanTiltCmd("tilt", -tilt_speed))
                self.key_states["s"] = True
            elif self.key_states["s"]: # if the key was unpressed
                self.key_states["s"] = False
                commands.append(PanTiltCmd("tilt", 0))

            if "d" in pressed_keys and not "a" in pressed_keys:
                commands.append(PanTiltCmd("pan", pan_speed))
                self.key_states["d"] = True
            elif self.key_states["d"]: # if the key was unpressed
                self.key_states["d"] = False
                commands.append(PanTiltCmd("pan", 0))

            if "f" in pressed_keys:
                commands.append(FireCmd(True))
                self.key_states["f"] = True
            elif self.key_states["f"]: # if the key was unpressed
                self.key_states["f"] = False
                commands.append(FireCmd(False))

            # if "j" in pressed_keys:
            #     commands.append(SpinCmd())
            #     self.key_states["j"] = True

            return commands
    
    def test_serial_echo(self, display):
        """
        Echo serial data that comes in to the display

        Args:
            display (Display): OLED display driver object
        """
        available = self.cmd_serial.in_waiting
        if available:
            line = self.get_line()
            display.text(line)

    def get_targeting_cmds(self, display:Display):
        # only attempt to get command if new serial line is available
        available = self.cmd_serial.in_waiting
        if available:
            line = self.get_line()
            display.text(line)
            cmd_args = line.split()   # will be any of:
                                      # ["SET", "PAN" "X.XX"] / ["SET", "TILT", "X.XX"]
                                      # ["SPIN", "UP"] / ["SPIN", "DOWN"]
                                      # ["SAFETY", "ON"] / ["SAFTEY", "OFF"]
                                      # ["FIRE"]
            
            if cmd_args[0] == "SET":
                # This is a stepper movement command
                if cmd_args[1] == "PAN":
                    # This is a pan stepper command
                    speed = float(cmd_args[2])
                    return PanTiltCmd("pan", speed)
                elif cmd_args[1] == "TILT":
                    # This is a tilt stepper command
                    return PanTiltCmd("tilt", speed)
                else:
                    # invalid command
                    display.text("INVALID SPIN")
                    raise(ValueError("Invalid SPIN command"))
                    return
            elif cmd_args[0] == "SPIN":
                # This is a flywheel spin command
                if cmd_args[1] == "UP":
                    # TODO: Spin flywheels up
                    return SpinCmd(True)
                elif cmd_args[1] == "DOWN":
                    # TODO: Spin flywheels down
                    return SpinCmd(False)
                else:
                    # invalid command
                    display.text("INVALID SET")
                    raise(ValueError("Invalid SET command"))
            elif cmd_args[0] == "SAFETY":
                if cmd_args[1] == "ON":
                    # This is a safety on command
                    return SafetyCmd(True)
                elif cmd_args[1] == "OFF":
                    # This is a safety off command
                    return SafetyCmd(False)
                else:
                    # invalid command
                    display.text("INVALID SAFETY")
                    raise(ValueError("Invalid SAFETY command"))
                    return
            elif cmd_args[0] == "FIRE":
                return FireCmd(True)
            else:
                # invalid command
                    display.text("INVALID COMMAND")
                    raise(ValueError("Invalid command"))
                    return
