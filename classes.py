""" all classes for nerf sentry project """
import math
import asyncio
import usb_cdc
import displayio
import busio
from adafruit_motor import servo
import adafruit_displayio_ssd1306
from adafruit_display_text import label
import terminalio
import pwmio
import board
from digitalio import DigitalInOut, Direction
from microcontroller import Pin


class Display:
    def __init__(self, sda:Pin, scl:Pin,
                 width:int, height:int, border:int,
                 invert:bool=False) -> None:
        """ setup OLED display

        Args:
            sda (Pin): SDA pin
            scl (Pin): SCL pin
            width (int): width of display in px
            height (int): height of display in px
            border (int): border around outside of display
            invert (bool, optional): display colors inverted. Defaults to False.
        """
        # free up all pins that may have previously been used for displays
        displayio.release_displays()

        # Use for I2C
        i2c = busio.I2C(scl=scl, sda=sda); display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)

        # setup display object
        self.WIDTH = width; self.HEIGHT = height; self.BORDER = border
        self.display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=self.WIDTH, height=self.HEIGHT)

        self.setup_canvas()

    def setup_canvas(self):
        # Make the display context
        self.splash = displayio.Group()
        self.display.show(self.splash)

        color_bitmap = displayio.Bitmap(self.WIDTH, self.HEIGHT, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = 0xFFFFFF  # White

        bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
        self.splash.append(bg_sprite)

        self.clear_canvas()
    
    def clear_canvas(self):
        # Draw a smaller inner rectangle
        inner_bitmap = displayio.Bitmap(self.WIDTH - self.BORDER * 2, self.HEIGHT - self.BORDER * 2, 1)
        inner_palette = displayio.Palette(1)
        inner_palette[0] = 0x000000  # Black
        inner_sprite = displayio.TileGrid(
            inner_bitmap, pixel_shader=inner_palette, x=self.BORDER, y=self.BORDER
        )
        self.splash.append(inner_sprite)

    def text(self, text):
        self.clear_canvas()
        # create text object
        text_area = label.Label(
            terminalio.FONT, text=text, color=0xFFFFFF, y=self.HEIGHT // 2 - 1
        )

        # place text in x center of screen
        text_width = text_area.width
        text_area.x = math.floor(self.WIDTH/2 - text_width/2)
        self.splash.append(text_area)


class PanTiltCmd:
    """
    Class that represents a stepper motor command for the pan/tilt mount on the sentry
    """

    def __init__(self, channel, speed) -> None:
        """
        Args:
            channel (string): "pan" for pan stepper, "tilt" for tilt stepper
            speed (float): -1 to +1. Fraction of the max speed to drive the channel at.
        """
        self.channel = channel
        self.speed = speed
    
    def __repr__(self):
        return f"{self.channel} Command with speed {self.speed}"
    
    def __eq__(self, other) : 
        return self.channel == other.channel
    
    def __hash__(self):
        return hash(self.channel)


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
        self.channel = "spin"
    
    def __repr__(self):
        return f"Spin Command with state {self.state}"

    def __eq__(self, other) : 
        return self.channel == other.channel
    
    def __hash__(self):
        return hash(self.channel)


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
        self.channel = "safety"
    
    def __repr__(self):
        return f"Safety Command with state {self.state}"

    def __eq__(self, other) : 
        return self.channel == other.channel
    
    def __hash__(self):
        return hash(self.channel)


class FireCmd:
    """
    Class that represents a fire command for the sentry trigger.
    """

    def __init__(self, state) -> None:
        self.state = state
        self.channel = "trigger"

    def __repr__(self):
        return "Fire Command"

    def __eq__(self, other) : 
        return self.channel == other.channel
    
    def __hash__(self):
        return hash(self.channel)


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
            # display.text(line)
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
                    return [PanTiltCmd("pan", speed)]
                elif cmd_args[1] == "TILT":
                    # This is a tilt stepper command
                    speed = float(cmd_args[2])
                    return [PanTiltCmd("tilt", speed)]
                else:
                    # invalid command
                    display.text("INVALID SET")
                    raise(ValueError("Invalid SET command"))
                    return
            elif cmd_args[0] == "SPIN":
                # This is a flywheel spin command
                if cmd_args[1] == "UP":
                    # TODO: Spin flywheels up
                    return [SpinCmd(True)]
                elif cmd_args[1] == "DOWN":
                    # TODO: Spin flywheels down
                    return [SpinCmd(False)]
                else:
                    # invalid command
                    display.text("INVALID SET")
                    raise(ValueError("Invalid SET command"))
            elif cmd_args[0] == "SAFETY":
                if cmd_args[1] == "ON":
                    # This is a safety on command
                    return [SafetyCmd(True)]
                elif cmd_args[1] == "OFF":
                    # This is a safety off command
                    return [SafetyCmd(False)]
                else:
                    # invalid command
                    display.text("INVALID SAFETY")
                    raise(ValueError("Invalid SAFETY command"))
                    return
            elif cmd_args[0] == "FIRE":
                return [FireCmd(True)]
            else:
                # invalid command
                    display.text("INVALID COMMAND")
                    raise(ValueError("Invalid command"))
                    return


class Sentry:
    """
    Object that represents all of the actuators in the NERF sentry turret
    """

    def __init__(self, step_res = [1, 1, 1]):
        """
        Initialize all control objects and move them to their correct positions
        """
        # define pins on the Raspberry Pi Pico
        self.MS1 = board.GP20
        self.MS2 = board.GP21
        self.MS3 = board.GP22
        self.PAN_STP = board.GP17
        self.PAN_DIR = board.GP16
        self.TILT_STP = board.GP13
        self.TILT_DIR = board.GP12
        self.HOLD = board.GP11
        self.TRIGGER_SERVO = board.GP15
        self.FLYWHEEL_RELAY = board.GP28
        self.SDA = board.GP26
        self.SCL = board.GP27

        # setup board led
        self.led = DigitalInOut(board.LED)
        self.led.direction = Direction.OUTPUT

        # setuo microstep config pins for the A4988 stepper driver
        self.ms1 = DigitalInOut(self.MS1)
        self.ms1.direction = Direction.OUTPUT  # ms1 (microstep config) pin
        self.ms2 = DigitalInOut(self.MS2)
        self.ms2.direction = Direction.OUTPUT  # ms2 (microstep config) pin
        self.ms3 = DigitalInOut(self.MS3)
        self.ms3.direction = Direction.OUTPUT  # ms3 (microstep config) pin

        # set microstep config
        self.set_step_res(microsteps[1/16])

        # setup motor control objects
        # stepper that moves pan  channel
        self.pan_stepper = Stepper(4950, self.PAN_STP,  self.PAN_DIR)
        # stepper that moves tilt channel
        self.tilt_stepper = Stepper(1694, self.TILT_STP, self.TILT_DIR)
        # object for enabling/disabling stepper hold mode
        self.stepper_hold = StepperHold(self.HOLD)
        # object for controlling flywheel and trigger pull
        self.sentry_trigger = Trigger(self.TRIGGER_SERVO, self.FLYWHEEL_RELAY)

        # setup display
        self.display = Display(self.SDA, self.SCL, width=128, height=32, border=0)

        # set to hold currently active commands and the tasks that are serving them
        self.cmds = set()
    
    def __del__(self):
        self.stepper_hold.toggle()

    def set_step_res(self, step_res_config):
        """
        Switch the step resolution of the stepper motors

        Args:
            step_res_config (tuple of bools): values to set the
            MS1, MS2, MS3 pins on the A4988 stepper driver board
        """
        self.ms1.value = step_res_config[0]
        self.ms2.value = step_res_config[1]
        self.ms3.value = step_res_config[2]

    async def blink_led(self, interval):
        """
        Infinitely blink the onboard led of the pico at a given interval

        Args:
            interval (float): blink interval in seconds
        """
        while True:
            self.led.value = True
            await asyncio.sleep(interval)
            self.led.value = False
            await asyncio.sleep(interval)
    
    async def execute_cmds(self):
        """
        Asynchronously execute all motor commands

        Args:
            cmd (Cmd message): the command to execute
        """

        # switch on command message type to execute different types of commands
        while True:
            await asyncio.sleep(0)
            for cmd in self.cmds:
                await asyncio.sleep(0)
                # print(cmd)
                if isinstance(cmd, PanTiltCmd):
                    channel = cmd.channel
                    speed = cmd.speed
                    stepper = self.pan_stepper if channel == "pan" else self.tilt_stepper
                    stepper.set_speed(speed)
                    self.cmds.discard(cmd)
                elif isinstance(cmd, SpinCmd):
                    # TODO
                    pass
                elif isinstance(cmd, SafetyCmd):
                    # TODO
                    pass
                elif isinstance(cmd, FireCmd):
                    if cmd.state == True:
                        print("FIRE")
                        asyncio.create_task(self.sentry_trigger.fire())
                        self.cmds.discard(cmd)
                        # await asyncio.gather(firetask)
                        # await asyncio.sleep(0)
                        # firetask.cancel()

    async def run_op_control(self, ser):
        """
        Handles getting commands from serial parser and passing them to the execution method

        Args:
            ser (SerialParser): serial parser for the command stream
        """
        while True:
            await asyncio.sleep(0)
            input_cmds = ser.get_op_control_cmds()
            if input_cmds:
                # print(input_cmds)
                # async sleep to hopefully make shit work?
                await asyncio.sleep(0)

                # update command set
                for cmd in input_cmds:
                    await asyncio.sleep(0)
                    self.cmds.discard(cmd)
                    self.cmds.add(cmd)

                print(self.cmds)
    
    async def run_targeting(self, ser:SerialParser):
        """
        Handles getting targeting commands from serial parser and passing them to the execution method

        Args:
            ser (SerialParser): serial parser for the command stream
        """
        while True:
            await asyncio.sleep(0)
            input_cmds = ser.get_targeting_cmds(self.display)
            if input_cmds:
                # async sleep to hopefully make shit work?
                await asyncio.sleep(0)

                # update command set
                for cmd in input_cmds:
                    # await asyncio.sleep(0)
                    self.cmds.discard(cmd)
                    self.cmds.add(cmd)

                print(self.cmds)

microsteps = {
    1: [0, 0, 0],
    1/2: [1,0, 0],
    1/4: [0,1, 0],
    1/8: [1,1, 0],
    1/16: [1,1, 1],
}

class A4988:
    def __init__(self, DIR:Pin, STEP:Pin, max_steps_per_second:int=2156):
        """
        This class represents an A4988 stepper motor driver.  It uses two output pins
        for direction and step control signals.

        Args:
            DIR (Pin): pin on board connected to A4988 DIR pin
            STEP (Pin): pin on board connected to A4988 STEP pin
            max_speed (int): max speed of 
        """
        # This class represents an A4988 stepper motor driver.  It uses two output pins
        # for direction and step control signals.
        self.max_steps_per_second = max_steps_per_second

        # setup pins
        self._dir  = DigitalInOut(DIR); self._dir.direction  = Direction.OUTPUT
        self._step = pwmio.PWMOut(STEP, variable_frequency=True)
        
    def set_speed_pwm(self, speed):
        """
        Set the driver to run its stepper motor indefinitely at a given speed

        Args:
            speed (float): ranges from -1 to +1. Fraction of the max speed to drive at
        """
        if speed == 0: # stop the driver and return if speed is 0
            self._step.duty_cycle = 0
            return
        else: # determine step PWM freqeuncy and set the driver in motion
            # flip direction of movement if necessary
            if speed < 0:
                self._dir.value = False
            else:
                self._dir.value = True
            
            self._step.duty_cycle = 65535 // 2 # set duty cycle to 1/2

            f = math.floor(self.max_steps_per_second * abs(speed))  # calculate pwm frequency as percentage of maximum
            self._step.frequency = f           # set pwm frequency of step pin

    def __enter__(self):
        return self

    def __exit__(self):
        """ Automatically deinitializes the hardware when exiting a context. """
        self._dir.deinit()
        self._step.deinit()
        self._dir  = None
        self._step = None

class Stepper:
    def __init__(self, steps_per_rev, step_pin, direction_pin):
        """
        Represents and controls turret stepper motor driven by an A4988 control board

        Args:
            steps_per_rev (int): number of steps to turn the axis 360 deg (PAN = 4950, TILT = 1694)
            step_pin (board.pin): Pico GPIO pin connected to A4988 step (STEP) pin
            direction_pin (board.pin): Pico GPIO pin connected to A4988 direction (DIR) pin
            hold_pin (board.pin): Pico GPIO pin connected to A4988 hold toggle (ENABLE) pin
        """
        # control params
        self.steps_per_rev = steps_per_rev

        # stepper controller
        self.driver = A4988(DIR=direction_pin, STEP=step_pin)
    
    def set_speed(self, speed):
        """
        Move the motor indefinitely at a given speed

        Args:
            speed (float): -1 to 1, multiple of max speed
        """
        self.driver.set_speed_pwm(speed)

class Trigger:
    def __init__(self, servo_pin, flywheel_pin):
        """
        Represents trigger puller mechanism of the NERF gun, driven by an MG996R hobby servo.

        Args:
            servo_pin (board.pin): pin on the Pico connected to the signal lead of the servo
        """
        # state parameters
        self.safety_on = False
        
        # Servo control object
        pwm = pwmio.PWMOut(servo_pin, duty_cycle=2 ** 15, frequency=50)
        self.servo = servo.Servo(pwm)

        # Flywheel motor relay control
        self.FLYWHEEL_ON = DigitalInOut(flywheel_pin)
        self.FLYWHEEL_ON.direction = Direction.OUTPUT
        self.FLYWHEEL_ON.value = False
    
    def toggle_safety(self):
        """
        Toggle the boolean state of trigger safety
        """
        self.safety_on = not self.safety_on
    
    async def fire(self):
        """
        Spin up flywheel if necessary and pull trigger servo to shoot one NERF dart
        """
        # if self.safety_on:
        #     await asyncio.sleep(0)
        #     return
        # spin up flywheels if necessary
        # if not self.FLYWHEEL_ON.value:
        self.FLYWHEEL_ON.value = True
        await asyncio.sleep(1.5)

        # pull trigger servo (only if it is in a retracted state)
        # if self.servo.angle < 10:
        self.servo.angle = 0
        await asyncio.sleep(1)
        self.servo.angle = 180
        await asyncio.sleep(.25)

        # spin down flywheels
        self.FLYWHEEL_ON.value = False
        await asyncio.sleep(0)

class StepperHold:
    def __init__(self, hold_pin):
        """
        Controls the hold function of the A4988 stepper driver

        Args:
            hold_pin (board.pin): Pico pin connected to the hold (ENABLE) pin of the A4988
        """
        # hold pin
        self.DISABLE_HOLD = DigitalInOut(hold_pin)
        self.DISABLE_HOLD.direction = Direction.OUTPUT
        self.DISABLE_HOLD.value = False
    
    def toggle(self):
        """
        Hold on powers the stepper to resist backdriving, hold off lets it spin freely.
        """
        self.DISABLE_HOLD.value = not self.DISABLE_HOLD.value

