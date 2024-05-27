import evdev
from evdev import InputDevice, categorize, ecodes
import subprocess
import time
import os
from collections import defaultdict
from threading import Timer

# Change this to the path of your joystick device
joystick_path = '/dev/input/event18'  # Or use the path found under /dev/input/by-id/

# Constants
PRESS_THRESHOLD = 5  # Number of presses required to trigger the command
RESET_TIME = 2  # Time in seconds to reset the press count

# Wait for the joystick device file to be available
while not os.path.exists(joystick_path):
    print(f"Waiting for device {joystick_path} to become available...")
    time.sleep(1)  # Wait for 1 second before checking again

# Attempt to initialize the joystick device
try:
    joystick = InputDevice(joystick_path)
    print(f"Device {joystick_path} found and initialized.")
except PermissionError:
    print(f"Permission denied: {joystick_path}. Try running the script with sudo.")
    exit(1)
except FileNotFoundError:
    print(f"Device {joystick_path} not found. Please check the device path.")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)

# Function to execute commands
def execute_command(command):
    try:
        subprocess.call(command, shell=True)
    except Exception as e:
        print(f"Failed to execute command '{command}': {e}")

# Mapping joystick buttons to commands
button_command_map = {
    305: 'gnome-terminal -- bash -c "ros2 launch turtlebot3_bringup turtlebot3.launch.py; exec bash"', 
    312: 'nmcli connection down lidar && nmcli connection up plc',
    310: 'nmcli connection down plc && nmcli connection up lidar',
    # Add more button mappings here if needed
}

# Track button presses
button_press_count = defaultdict(int)
button_timers = {}

# Reset button press count after a period of inactivity
def reset_button_press_count(button_code):
    button_press_count[button_code] = 0

print("Listening for joystick events...")

# Event loop to listen for joystick events
for event in joystick.read_loop():
    if event.type == ecodes.EV_KEY:  # Check if the event is a key press
        key_event = categorize(event)
        print(f"Key event detected: {key_event}")  # Debug: print key event details
        if key_event.keystate == key_event.key_down:  # Check if the key state is 'down'
            button_code = key_event.scancode
            button_press_count[button_code] += 1
            print(f"Button {button_code} pressed {button_press_count[button_code]} times")  # Debug: press count

            # Cancel any existing timer for this button and start a new one
            if button_code in button_timers:
                button_timers[button_code].cancel()
            button_timers[button_code] = Timer(RESET_TIME, reset_button_press_count, [button_code])
            button_timers[button_code].start()

            if button_press_count[button_code] >= PRESS_THRESHOLD:
                command = button_command_map.get(button_code)  # Get the command for the scancode
                if command:
                    print(f"Executing command: {command}")
                    execute_command(command)
                else:
                    print(f"No command mapped for button code: {button_code}")  # Debug: unmapped button press
                button_press_count[button_code] = 0  # Reset count after command execution
