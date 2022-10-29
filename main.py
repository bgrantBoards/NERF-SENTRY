# import serial
import asyncio
from sentry import Sentry
from cmd_listener import SerialParser

# from motor_test import main

s = Sentry()
ser = SerialParser()


async def main():
    led_task = asyncio.create_task(s.blink_led(0.08))
    serial_task = asyncio.create_task(ser.listen())

    await asyncio.gather(led_task, serial_task)  # Don't forget "await"!
    # await asyncio.gather(led_task)  # Don't forget "await"!
    print("done")

asyncio.run(main())
