#!/usr/bin/env python3
"""
MQTT Relay Controller

This script listens for MQTT messages on a specified topic and uses those messages
to control a relay connected to a Raspberry Pi via a GPIO pin. It supports robust
MQTT connection handling with automatic reconnection attempts using exponential backoff,
and it gracefully cleans up resources on shutdown.

Features:
- MQTT integration with automatic reconnection logic and exponential backoff
- Relay control via Raspberry Pi GPIO
- Detailed logging for debugging and operational monitoring
- Graceful shutdown via signal handling

Author: Seth Morrow
Date: 2-7-2025
"""

import time
import signal
import sys
import logging
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from typing import Dict, Any

# ----------------------------
# Configuration Section
# ----------------------------

# Define the GPIO pin connected to the relay
RELAY_PIN = 17  # Use BCM numbering; update if using a different GPIO pin

# MQTT broker configuration
MQTT_BROKER = "192.168.1.100"  # Replace with your MQTT broker's IP address or hostname
MQTT_PORT = 1883               # Standard MQTT port
MQTT_TOPIC = "plc/control"     # MQTT topic to subscribe for power control commands
MQTT_KEEPALIVE = 60            # Keep-alive time in seconds

# Define the messages that trigger power actions
POWER_ON_MESSAGE = "power on"
POWER_OFF_MESSAGE = "power off"

# ----------------------------
# Logging Setup
# ----------------------------

# Configure the logging system to output debug information to the console.
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more verbose output if needed.
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ----------------------------
# GPIO Setup and Cleanup Functions
# ----------------------------

def setup_gpio() -> None:
    """
    Initialize the Raspberry Pi GPIO settings for the relay.

    This function sets the GPIO numbering mode, configures the relay pin as an output,
    and initializes the relay to the OFF state.
    """
    GPIO.setmode(GPIO.BCM)              # Use Broadcom pin numbering system.
    GPIO.setup(RELAY_PIN, GPIO.OUT)       # Configure the relay pin as an output.
    # For an active HIGH relay:
    # - GPIO.HIGH activates the relay (device is powered on).
    # - GPIO.LOW deactivates the relay (device is powered off).
    GPIO.output(RELAY_PIN, GPIO.LOW)      # Start with the device powered off.
    logger.info("GPIO has been set up. Relay is initialized to OFF state.")

def cleanup_gpio() -> None:
    """
    Clean up the Raspberry Pi GPIO settings.

    This function resets all GPIO channels that have been used by this program.
    It should be called upon program exit to ensure that the GPIO pins are left in a safe state.
    """
    GPIO.cleanup()
    logger.info("GPIO cleanup complete. All GPIO channels have been reset.")

# ----------------------------
# MQTT Callback Functions
# ----------------------------

def on_connect(client: mqtt.Client, userdata: Any, flags: Dict[str, Any], rc: int) -> None:
    """
    Callback function for when the MQTT client connects to the broker.

    Parameters:
      client   : The MQTT client instance.
      userdata : User defined data (not used here).
      flags    : Response flags sent by the broker.
      rc       : The connection result (0 means success).

    This function subscribes to the designated topic upon a successful connection.
    """
    if rc == 0:
        logger.info("Successfully connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to MQTT topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")

def on_disconnect(client: mqtt.Client, userdata: Any, rc: int) -> None:
    """
    Callback function for when the MQTT client disconnects from the broker.

    Parameters:
      client   : The MQTT client instance.
      userdata : User defined data (not used here).
      rc       : The disconnection result code.

    This function logs a warning if the disconnection was unexpected (rc != 0).
    """
    if rc != 0:
        logger.warning("Unexpected MQTT disconnection. The client will attempt to reconnect.")
    else:
        logger.info("MQTT client disconnected successfully.")

def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    """
    Callback function for when an MQTT message is received.

    Parameters:
      client   : The MQTT client instance.
      userdata : User defined data (not used here).
      msg      : The MQTT message instance, containing topic and payload.

    This function decodes the incoming message and controls the relay based on the command received.
    """
    try:
        # Decode the incoming message payload to a UTF-8 string and standardize it to lower case.
        message = msg.payload.decode("utf-8").strip().lower()
        logger.info(f"Received message on topic '{msg.topic}': {message}")

        # Check if the message instructs to turn the device on or off.
        if message == POWER_ON_MESSAGE:
            logger.info("Power on command received. Activating the relay...")
            GPIO.output(RELAY_PIN, GPIO.HIGH)  # Activate the relay (power on).
            logger.info("Relay activated. The device is now powered on.")
        elif message == POWER_OFF_MESSAGE:
            logger.info("Power off command received. Deactivating the relay...")
            GPIO.output(RELAY_PIN, GPIO.LOW)   # Deactivate the relay (power off).
            logger.info("Relay deactivated. The device is now powered off.")
        else:
            logger.warning("Received an unrecognized command. No action taken.")
    except UnicodeDecodeError:
        logger.error(f"Failed to decode message payload on topic '{msg.topic}'")
    except GPIO.error as e:
        logger.error(f"GPIO error: {e}")
    except Exception as e:
        logger.exception(f"Exception occurred while processing the message: {e}")

# ----------------------------
# MQTT Connection with Retry Logic
# ----------------------------

def connect_with_retry(client: mqtt.Client, broker: str, port: int, max_retries: int = 5) -> bool:
    """
    Attempt to connect to the MQTT broker with a retry mechanism using exponential backoff.

    Parameters:
      client      : The MQTT client instance.
      broker      : The hostname or IP address of the MQTT broker.
      port        : The port number for the MQTT broker.
      max_retries : The maximum number of retry attempts before giving up.

    Returns:
      True if the connection was successful, False otherwise.
    """
    retry_interval = 1  # Start with a 1-second wait between retries.
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1} of {max_retries}: Connecting to MQTT broker at {broker}:{port}...")
            client.connect(broker, port, MQTT_KEEPALIVE)
            logger.info("Connected to MQTT broker successfully.")
            return True  # Connection succeeded.
        except Exception as e:
            logger.exception(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
                retry_interval *= 2  # Exponential backoff.
    logger.error("Maximum connection attempts reached. Could not connect to the MQTT broker.")
    return False

# ----------------------------
# Signal Handling for Graceful Shutdown
# ----------------------------

def signal_handler(signum: int, frame: Any) -> None:
    """
    Handle termination signals to allow for graceful shutdown.

    Parameters:
      signum : The signal number.
      frame  : The current stack frame (not used).

    This function cleans up the GPIO and exits the program.
    """
    logger.info("Shutdown signal received. Initiating cleanup...")
    cleanup_gpio()
    sys.exit(0)

# ----------------------------
# Main Program Execution
# ----------------------------

def main() -> None:
    """
    Main function that initializes the system, sets up the MQTT client and GPIO, and starts the network loop.

    This function configures signal handlers for graceful shutdown, establishes the MQTT connection
    (with retries), and enters the MQTT loop to process incoming messages continuously.
    """
    # Register signal handlers for SIGINT and SIGTERM to enable graceful shutdown.
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize the GPIO for controlling the relay.
    setup_gpio()

    # Create an instance of the MQTT client and set up callbacks.
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # Attempt to connect to the MQTT broker with retry logic.
    if not connect_with_retry(client, MQTT_BROKER, MQTT_PORT):
        cleanup_gpio()
        sys.exit(1)  # Exit if connection attempts fail.

    try:
        # Start the MQTT network loop which will run indefinitely and handle reconnections automatically.
        logger.info("Entering MQTT loop to listen for messages...")
        client.loop_forever()
    except Exception as e:
        logger.exception(f"An exception occurred during the MQTT loop: {e}")
    finally:
        # Ensure that the MQTT client disconnects and GPIO is cleaned up upon exit.
        client.disconnect()
        cleanup_gpio()
        logger.info("Program is exiting. Resources have been cleaned up.")

if __name__ == "__main__":
    main()
