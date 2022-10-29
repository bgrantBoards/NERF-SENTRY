import usb_cdc
import asyncio


class PanTiltCmd:
    """
    Class that represents a stepper motor command for the pan/tilt mount on the sentry
    """

    def __init__(self, axis, speed) -> None:
        """
        Args:
            axis (string): "pan" for pan stepper, "tilt" for tilt stepper
            speed (float): -1 to +1. Fraction of the max speed to drive the axis at.
        """
        self.axis = axis
        self.speed = speed
    
    def __repr__(self):
        return f"{self.axis} Command with speed {self.speed}"


class SpinCmd:
    """
    Class that represents a flywheel spin command for the sentry
    """

    def __init__(self, state) -> None:
        """
        Args:
            state (bool): True for spin up, False for spin down
        """
        self.state = state
    
    def __repr__(self):
        return f"Spin Command with state {self.state}"


class SafetyCmd:
    """
    Class that represents a trigger safety command for the sentry
    """

    def __init__(self, state) -> None:
        """
        Args:
            state (bool): True for safe on (trigger lock), False for safe off
        """
        self.state = state
    
    def __repr__(self):
        return f"Safety Command with state {self.state}"


class FireCmd:
    """
    Class that represents a fire command for the sentry trigger.
    """

    def __init__(self) -> None:
        # There is supposed to be nothing here becasue a fire command encodes all
        # of its information through simply existing
        pass

    def __repr__(self):
        return "Fire Command"


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

    async def op_control(self):
        """
        Listens for operator keyboard controls from the host serial connection and returns command messages.
        """
        test_speed = 0.1
        key_states = {
            "w": False,
            "a": False,
            "s": False,
            "d": False,
            "f": False,
            "j": False,
        }
        while True:
            # dummy delay to make async work
            await asyncio.sleep(0)

            # only get lines from serial if there are new lines to get
            available = self.cmd_serial.in_waiting
            if available:
                # get a line and begin parsing
                # key press data in from op control line by line in this format: "{'j', 'a', 'g', 'h'}"
                pressed_keys = self.cmd_serial.readline()[:-1].decode("utf-8").split("'")

                # pop out characters that we don't want to consider
                for idx, c in enumerate(pressed_keys):
                    if not c.islower():
                        pressed_keys.pop(idx)

                # switch on characters to get commands
                commands = []
                if "w" in pressed_keys and not "s" in pressed_keys:
                    # commands.append("up")
                    commands.append(PanTiltCmd("tilt", test_speed))
                    key_states["w"] = True
                elif key_states["w"] == True: # if the key was unpressed
                    key_states["w"] = False
                    commands.append(PanTiltCmd("tilt", 0))

                if "a" in pressed_keys and not "d" in pressed_keys:
                    commands.append(PanTiltCmd("pan", -test_speed))
                    key_states["a"] = True
                elif key_states["a"] == True: # if the key was unpressed
                    key_states["a"] = False
                    commands.append(PanTiltCmd("pan", 0))

                if "s" in pressed_keys and not "w" in pressed_keys:
                    commands.append(PanTiltCmd("tilt", -test_speed))
                    key_states["s"] = True
                elif key_states["s"] == True: # if the key was unpressed
                    key_states["s"] = False
                    commands.append(PanTiltCmd("tilt", 0))

                if "d" in pressed_keys and not "a" in pressed_keys:
                    commands.append(PanTiltCmd("pan", test_speed))
                    key_states["d"] = True
                elif key_states["d"] == True: # if the key was unpressed
                    key_states["d"] = False
                    commands.append(PanTiltCmd("pan", 0))

                if "f" in pressed_keys:
                    commands.append("fire")
                    key_states["f"] = True

                if "j" in pressed_keys:
                    commands.append("toggle spin")
                    key_states["j"] = True

                if commands:
                    print(commands)
                    return commands
                else:
                    print("")
