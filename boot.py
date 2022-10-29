import usb_midi
import usb_cdc

usb_midi.disable()
usb_cdc.enable(console=True, data=True)    # Enable console and data
