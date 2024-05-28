#!/bin/bash

joystick_path="/dev/input/event18"
PRESS_THRESHOLD=5  # Number of presses required to trigger the command
RESET_TIME=2  # Time in seconds to reset the press count

declare -A button_press_count
declare -A button_last_press_time

# Mapping joystick buttons to commands
declare -A button_command_map=(
   305='gnome-terminal -- bash -c "ros2 launch turtlebot3_bringup turtlebot3.launch.py; exec bash"'
    17='nmcli connection down lidar && nmcli connection up plc'
    16='nmcli connection down plc && nmcli connection up lidar'
    # Add more button mappings here if needed
)

reset_button_press_count() {
    for button_code in "${!button_press_count[@]}"; do
        current_time=$(date +%s)
        if (( current_time - button_last_press_time[$button_code] > RESET_TIME )); then
            button_press_count[$button_code]=0
        fi
    done
}

execute_command() {
    local command=$1
    echo "Attempting to execute command: $command"
    eval "$command"
    if [ $? -eq 0 ]; then
        echo "Command executed successfully: $command"
    else
        echo "Failed to execute command: $command"
    fi
}

echo "Listening for joystick events on $joystick_path..."

sudo evtest "$joystick_path" | while read -r line; do
    echo "Event detected: $line"  # Debug: print all events

    if [[ $line =~ EV_KEY ]]; then
        button_code=$(echo $line | awk '{print $6}' | tr -d ',')
        button_state=$(echo $line | awk '{print $8}')

        if [[ $button_state == "1" ]]; then
            button_press_count[$button_code]=$((button_press_count[$button_code] + 1))
            button_last_press_time[$button_code]=$(date +%s)
            echo "Button $button_code pressed ${button_press_count[$button_code]} times"

            reset_button_press_count

            if [[ ${button_press_count[$button_code]} -ge $PRESS_THRESHOLD ]]; then
                command=${button_command_map[$button_code]}
                if [[ -n $command ]]; then
                    execute_command "$command"
                else
                    echo "No command mapped for button code: $button_code"
                fi
                button_press_count[$button_code]=0
            fi
        fi
    fi
done
