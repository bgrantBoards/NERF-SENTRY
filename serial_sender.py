import serial
import time
# ser = serial.Serial("/dev/tty.usbmodem142103")  # open first serial port


def send_line(ser_object, line):
    """
        Send a line to the pico via serial connection

        Args:
            line (string): 1-line message to send, no return character
        """
    ser_object.write(bytes(line + "\n", "utf_8"))      # write a string


test_commands = [
                 "SET PAN 0.1",
                 "SET PAN -0.1",
                 "SET PAN 0",
                 "SET TILT 0.1",
                 "SET TILT -0.1",
                 "SET TILT 0",
                 "FIRE"
                ]

with serial.Serial("/dev/tty.usbmodem142303") as ser:  # open serial port
    for cmd in test_commands:
        send_line(ser, cmd)
        print(f"{cmd} sent")
        time.sleep(1)

