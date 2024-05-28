import evdev
from evdev import InputDevice, categorize, ecodes


devices = [InputDevice(path) for path in evdev.list_devices()]
for device in devices:
    print(f"Device name: {device.name}, Device path: {device.path}")
