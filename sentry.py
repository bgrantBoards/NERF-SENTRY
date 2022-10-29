# Code to drive the Comp-Robo robotic sentry NERF gun turret
# Run on a Raspberry Pi Pico with Circuitpy installed

# load standard modules
import math
import asyncio
import board
from digitalio import DigitalInOut, Direction

# load custom modules
from actuators import Stepper, StepperHold, Trigger, microsteps

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
        # stepper that moves pan  axis
        self.pan_stepper = Stepper(4950, self.PAN_STP,  self.PAN_DIR)
        # stepper that moves tilt axis
        self.tilt_stepper = Stepper(1694, self.TILT_STP, self.TILT_DIR)
        # object for enabling/disabling stepper hold mode
        self.stepper_hold = StepperHold(self.HOLD)
        # object for controlling flywheel and trigger pull
        self.sentry_trigger = Trigger(self.TRIGGER_SERVO, self.FLYWHEEL_RELAY)

        # dictionary to hold currently active commands and the tasks that are serving them
            cmds_and_tasks = {}
    
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

    async def motor_test_async(self):
        # test trigger
        self.sentry_trigger.toggle_safety()
        print("safety off: firing")
        trigger_task = asyncio.create_task(self.sentry_trigger.fire())

        # test steppers
        print("moving steppers")
        pan_task1 = asyncio.create_task(self.pan_stepper.move(500, 400))
        tilt_task1 = asyncio.create_task(self.tilt_stepper.move(500, 400))
        await asyncio.gather(pan_task1, tilt_task1)

        # pan_task2 = asyncio.create_task(pan_stepper.move(2000, -400))
        # tilt_task2 = asyncio.create_task(tilt_stepper.move(500, -400))
        # await asyncio.gather(pan_task2, tilt_task2)

        # finish test
        self.stepper_hold.toggle()

    async def blink_led(self, interval):
        """
        Infinitely blink the onboard led of the pico at a given interval

        Args:
            interval (float): blink interval in seconds
        """
        while True:
            self.led.value = True
            # time.sleep(interval)
            await asyncio.sleep(interval)
            self.led.value = False
            # time.sleep(interval)
            await asyncio.sleep(interval)
    
    async def execute_cmd(self, cmd):
        """
        Asynchronously execute a motor command

        Args:
            cmd (Cmd message): the command to execute
        """
        # debug
        print(f"Executing: {cmd}")

        # switch on command message type to execute different commands
        if isinstance(cmd, PanTiltCmd):
            axis = cmd.axis
            speed = cmd.speed
            stepper = self.pan_stepper if axis == "pan" else self.tilt_stepper
            await asyncio.gather(stepper.set_speed(speed))

    async def run_op_control(sentry):
        while True:
            # async sleep to hopefully make shit work?
            await asyncio.sleep(0)

            # collecting and asynchronously starting new commands
            for cmd in ser.get_op_control_cmds():
                print("got a cmd!")
                for cmd in cmds:
                    if isinstance(cmd, PanTiltCmd)
                    current_cmds = 
                    tasks.append(asyncio.create_task(sentry.execute_cmd(cmd)))
                print(cmds)
            # await asyncio.gather(*tasks)
            # await asyncio.sleep(0)
