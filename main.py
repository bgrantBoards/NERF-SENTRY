# import serial
import asyncio
from sentry import Sentry
from cmd_listener import SerialParser

# from motor_test import main

s = Sentry()
ser = SerialParser()

# async def run_executor():
#     while True:


async def main():
    # led_task = asyncio.create_task(s.blink_led(0.08))
    # op_control = asyncio.create_task(ser.parse_commands())
    # op_control = asyncio.create_task(run_op_control())
    # executor = asyncio.create_task()

    # await asyncio.gather(led_task, op_control)  # Don't forget "await"!
    await asyncio.gather(s.blink_led(0.08), s.run_op_control())  # Don't forget "await"!
    # await asyncio.gather(led_task)  # Don't forget "await"!
    print("done")

try:
    asyncio.run(main())
except:
    print("del")
    s.stepper_hold.toggle()
    while True:
        pass