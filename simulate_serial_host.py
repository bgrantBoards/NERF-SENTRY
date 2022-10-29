from encodings import utf_8
import serial
import keyboard
ser = serial.Serial("/dev/tty.usbmodem142103")  # open first serial port


def send_line(line):
    """
    Send a line to the pico via serial connection

    Args:
        line (string): 1-line message to send, no return character
    """
    ser.write(bytes(line + "\n", "utf_8"))      # write a string


# while True:
#     keyboard.aaa
#     if keyboard.is_pressed("a"):
#         # print("You pressed 'a'.")
#         send_line("You pressed 'a'.")
#         # break

with keyboard.Listener(on_release=on_key_release) as listener:
    listener.join()

ser.close()             # close port
