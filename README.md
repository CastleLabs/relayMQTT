# Raspberry Pi MQTT Relay Controller - Setup and Usage Guide

This guide explains how to set up and use the MQTT Relay Controller script on your Raspberry Pi to control devices via a relay based on MQTT messages.

## Overview

The MQTT Relay Controller is a Python script that:
- Listens for commands over MQTT (a lightweight messaging protocol)
- Controls a relay connected to a Raspberry Pi GPIO pin
- Provides robust connection handling with automatic reconnection
- Includes detailed logging for monitoring and debugging
- Handles graceful shutdown when terminated

This system allows you to remotely control power to devices connected to the relay, such as lights, appliances, motors, or other electrical equipment.

## Hardware Requirements

1. Raspberry Pi (any model with GPIO pins)
2. Relay module (compatible with Raspberry Pi GPIO voltage)
3. Jumper wires to connect the relay to the Pi
4. Device to be controlled by the relay
5. Access to an MQTT broker on your network

## Software Requirements

1. Raspberry Pi OS (formerly Raspbian)
2. Python 3
3. Required Python packages:
   - `paho-mqtt` (MQTT client library)
   - `RPi.GPIO` (GPIO control library)

## Installation

### 1. Install Required Packages

```bash
sudo apt update
sudo apt install -y python3-pip
pip3 install paho-mqtt RPi.GPIO
```

### 2. Copy the Script

Create a new file on your Raspberry Pi:

```bash
nano mqtt_relay_controller.py
```

Copy and paste the entire script content, then save with Ctrl+O and exit with Ctrl+X.

### 3. Make the Script Executable

```bash
chmod +x mqtt_relay_controller.py
```

## Configuration

Before running the script, you should modify the following configuration variables in the code to match your setup:

### GPIO Configuration
```python
# Define the GPIO pin connected to the relay
RELAY_PIN = 17  # Use BCM numbering; update if using a different GPIO pin
```

Change `RELAY_PIN` to match the GPIO pin number where your relay is connected.

### MQTT Configuration
```python
# MQTT broker configuration
MQTT_BROKER = "192.168.1.100"  # Replace with your MQTT broker's IP address or hostname
MQTT_PORT = 1883               # Standard MQTT port
MQTT_TOPIC = "plc/control"     # MQTT topic to subscribe for power control commands
MQTT_KEEPALIVE = 60            # Keep-alive time in seconds
```

Update these settings with:
- Your MQTT broker's IP address or hostname
- The correct port (1883 is standard)
- The topic you want to use for sending commands

### Command Messages
```python
# Define the messages that trigger power actions
POWER_ON_MESSAGE = "power on"
POWER_OFF_MESSAGE = "power off"
```

These are the exact text messages that will trigger the relay to turn on or off. You can customize these if needed.

## Wiring the Relay

1. Connect the relay module to your Raspberry Pi:
   - VCC pin on relay → 5V or 3.3V on Pi (check relay specifications)
   - GND pin on relay → Ground pin on Pi
   - IN pin on relay → GPIO pin 17 (or whichever pin you configured)

2. Connect your controlled device to the relay:
   - The relay has terminals typically marked NO (Normally Open), NC (Normally Closed), and COM (Common)
   - For a device you want to be off when the relay is inactive:
     - Connect power through the NO and COM terminals

## Running the Script

### Manual Execution

Run the script with:

```bash
./mqtt_relay_controller.py
```

The script will output logs to the console.

### Running as a Service

For automatic startup when your Raspberry Pi boots, create a systemd service:

1. Create a service file:
```bash
sudo nano /etc/systemd/system/mqtt-relay.service
```

2. Add the following content:
```
[Unit]
Description=MQTT Relay Controller
After=network.target

[Service]
ExecStart=/path/to/mqtt_relay_controller.py
WorkingDirectory=/path/to/directory
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

3. Update paths in the service file to match your setup

4. Enable and start the service:
```bash
sudo systemctl enable mqtt-relay.service
sudo systemctl start mqtt-relay.service
```

5. Check status:
```bash
sudo systemctl status mqtt-relay.service
```

## Sending Commands

To control the relay, you need to publish MQTT messages to the configured topic (`plc/control` by default).

### Using MQTT Client Tools

Using `mosquitto_pub` (a command-line MQTT client):

```bash
# Turn on
mosquitto_pub -h 192.168.1.100 -t "plc/control" -m "power on"

# Turn off
mosquitto_pub -h 192.168.1.100 -t "plc/control" -m "power off"
```

Replace `192.168.1.100` with your MQTT broker's address.

### Using Mobile Apps

Several MQTT client apps are available for smartphones:
- MQTT Dashboard (Android)
- MQTTool (iOS)
- IoT MQTT Panel (Android)

Configure these with your broker details and publish the control messages.

### Using Home Automation Systems

Most home automation systems support MQTT, including:
- Home Assistant
- Node-RED
- OpenHAB

Configure these to publish to your MQTT topic to integrate the relay with your automation rules.

## Understanding the Code

The script is structured into several sections:

1. **Configuration**: Defines GPIO pins, MQTT settings, and control messages
2. **GPIO Setup**: Initializes the relay pin and sets its initial state (off)
3. **MQTT Callbacks**: Functions that handle MQTT connection events and messages
4. **Connection Logic**: Implements automatic reconnection with exponential backoff
5. **Signal Handling**: Ensures graceful shutdown when the script is terminated
6. **Main Loop**: Starts the MQTT client and keeps it running

## Troubleshooting

### Relay Not Responding
- Check GPIO pin configuration
- Verify relay wiring
- Ensure you're publishing to the correct MQTT topic
- Check the script logs for errors

### MQTT Connection Issues
- Verify MQTT broker address and port
- Check if the MQTT broker is running
- Ensure there are no network firewall restrictions
- Review the script logs for connection errors

### Script Crashes
- Check the logs for Python exceptions
- Verify all required packages are installed
- Ensure the Raspberry Pi has a stable power supply

## Potential Uses

This MQTT Relay Controller can be used for numerous applications:

1. **Home Automation**
   - Control lights, fans, or appliances remotely
   - Integrate with smart home systems via MQTT

2. **Agriculture/Gardening**
   - Automate irrigation systems
   - Control greenhouse equipment

3. **Industrial Control**
   - Remotely power equipment on/off
   - Integrate with industrial automation systems

4. **Energy Management**
   - Control high-consumption devices based on electricity rates
   - Implement load shedding during peak energy usage

5. **Security Systems**
   - Control electric locks or gates
   - Activate security lighting

6. **Remote Monitoring Stations**
   - Power cycle equipment remotely when issues occur
   - Manage power to sensors or cameras

7. **Aquarium/Terrarium Control**
   - Manage lighting cycles
   - Control heaters, pumps, or filters

8. **Computer Lab Management**
   - Remote power control for computers or network equipment
   - Scheduled power on/off for energy saving

## Advanced Customization

The script can be extended with additional features:

1. **Multiple Relays**
   - Add more GPIO pins and relay controls
   - Extend the message format to specify which relay to control

2. **Authentication**
   - Add MQTT username/password support
   - Implement TLS encryption for MQTT communication

3. **Status Reporting**
   - Publish the current state of relays to status topics
   - Implement periodic health check messages

4. **Web Interface**
   - Add a simple web server to view status and control relays
   - Create a dashboard for monitoring

5. **Time-Based Control**
   - Implement scheduling features
   - Add sunset/sunrise calculations for lighting control

## Safety Considerations

When working with relays and electrical devices:

1. **Electrical Safety**
   - Never work with mains voltage unless properly qualified
   - Use appropriate fuses and circuit protection
   - Consider using optically isolated relays for added safety

2. **Fail-Safe Design**
   - Consider what should happen if the Pi loses power or crashes
   - For critical applications, use normally-closed relays if appropriate

3. **Testing**
   - Test thoroughly with safe loads before connecting critical equipment
   - Verify behavior during power outages and network disconnections

## Conclusion

The MQTT Relay Controller provides a reliable and flexible way to control devices using a Raspberry Pi and MQTT messaging. With proper setup and configuration, it can be integrated into various systems and applications to enable remote control and automation.
