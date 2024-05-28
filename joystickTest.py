import evdev
from evdev import InputDevice, categorize, ecodes
import subprocess
import time
import os
from collections import defaultdict
from threading import Timer

# Constants
PRESS_THRESHOLD = 5  # Number of presses required to trigger the command
RESET_TIME = 2  # Time in seconds to reset the press count

# Function to find the joystick device
def find_joystick_device():
    devices = [InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        # Replace with the actual name of your joystick
        if 'DualSense Wireless Controller' or 'Wireless Controller' in device.name:  
            return device.path
    return None

joystick_path = find_joystick_device()

# Wait for the joystick device file to be available
while joystick_path is None:
    print(f"Waiting for joystick to become available...")
    time.sleep(1)  # Wait for 1 second before checking again
    joystick_path = find_joystick_device()

print(f"Device found at {joystick_path}")

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

# Function to terminate the process
def terminate_command():
    global process
    if process:
        try:
            process.terminate()
            process.wait()  # Wait for the process to terminate
            print("Process terminated.")
        except Exception as e:
            print(f"Failed to terminate the process: {e}")
        finally:
            process = None

# Mapping joystick buttons to commands
button_command_map = {
    317: 'gnome-terminal -- bash -c "ros2 launch turtlebot3_bringup turtlebot3.launch.py; exec bash"', 
    17: 'nmcli connection down lidar && nmcli connection up plc',
    16: 'nmcli connection down plc && nmcli connection up lidar',
    # Add more button mappings here if needed
}

terminate_button_code = 306  # Define a button code to terminate the process

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
            
            if button_code == terminate_button_code:
                terminate_command()
            else:
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
    elif event.type == ecodes.EV_ABS:  # Check if the event is an absolute axis event (e.g., joystick movement)
        abs_event = categorize(event)
        print(f"Absolute event detected: {abs_event}")  # Debug: print absolute event details
