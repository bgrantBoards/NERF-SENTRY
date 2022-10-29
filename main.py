# import serial
import asyncio
from sentry import Sentry
from cmd_listener import SerialParser

# from motor_test import main

s = Sentry()
ser = SerialParser()

asyncio.run(ser.listen())
