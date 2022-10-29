import usb_cdc
import asyncio
import time

class SerialParser:
    """
    Class that handles all serial communication with the Raspi host.
    Raspi will send motor commands to the pico, this class will handle
    recieving and parsing those commands.
    """
    def __init__(self) -> None:
        # define serial protocol command names
        self.commands = {
            "SET" :   ["PAN", "TILT"],
            "SPIN":   ["UP", "DOWN"],
            "SAFETY": ["ON", "OFF"],
            "FIRE":   []
        }

        # setup serial connection
        self.cmd_serial = usb_cdc.data

    async def listen(self):
        """
        Listens for new lines coming in from the serial connection
        """
        while True:
        #    await asyncio.sleep(.1)
        #    time.sleep(.1)
           line = self.cmd_serial.readline()[:-1]
           print(line)

        