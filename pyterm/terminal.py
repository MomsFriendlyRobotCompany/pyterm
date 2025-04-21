#!/usr/bin/env python3
##############################################
# The MIT License (MIT)
# Copyright (c) 2025 Kevin Walchko
# see LICENSE for full details
##############################################
import serial
import sys
import threading
import time
import termios
import tty
import select
import os
import platform
from colorama import Fore
import serial.tools.list_ports

def list_serial_ports():
    # Get a list of available serial ports
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("No serial ports found.")
        return
    
    print("Available serial ports:")
    for port in ports:
        print(f"{port.description}: {port.device}")
        # print(f"Port: {port.device}")
        # print(f"  Description: {port.description}")
        # print(f"  Hardware ID: {port.hwid}")
        # print(f"  Manufacturer: {port.manufacturer}")
        # print()

run = True

def get_key():
    """Read a single keypress from the terminal without echoing (macOS/Linux)."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        # Check if input is available (non-blocking)
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        if rlist:
            key = sys.stdin.read(1)
            return key
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def serial_read(ser):
    """Read data from the serial port and print it to the console."""
    global run

    while run:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            sys.stdout.write(data)
            sys.stdout.flush()
        time.sleep(0.1)
        
    # print("serial_read exit")

def serial_write(ser):
    """Read user input from the console and write it to the serial port."""
    global run

    buffer = ""

    while run:
        char = get_key()

        if char:
            if char == '\x03':  # Ctrl+C
                print(f"{Fore.YELLOW}---------------------\nCTRL-C ... exiting\n---------------------{Fore.RESET}")
                run = False

            if char != '\r':
                buffer += char
            elif char == '\r':  # Enter key
                if len(buffer) == 0:
                    continue
                    
                buffer += '\n'
                ser.write(buffer.encode('utf-8'))

                sys.stdout.write(f"{Fore.CYAN}>> {buffer}{Fore.RESET}")
                sys.stdout.flush()

                buffer = ""
            
    # print("serial_write exit")

def main():
    global run

    if len(sys.argv) != 3:
        print(f"{Fore.RED}Usage:")
        print(f" {sys.argv[0]} <serial_port> <baudrate>")
        print(f"{Fore.RESET}")
        sys.exit(1)

    port = sys.argv[1]
    baudrate = sys.argv[2]
    timeout = 0.1

    # Initialize serial connection
    try:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        print(f"{Fore.YELLOW}", end="")
        print("////////////////////////////////////////////////////////")
        print(f"// Platform: {platform.platform()}")
        print(f"// Connected to {port} at {baudrate} baud.")
        print("//")
        print("// Press Ctrl+C to exit.")
        print("////////////////////////////////////////////////////////")
        print(f"{Fore.RESET}")
    except serial.SerialException as e:
        print(f"{Fore.RED}Error opening serial port: {e}{Fore.RESET}")
        sys.exit(1)

    # Start separate threads for reading and writing
    read_thread = threading.Thread(target=serial_read, args=(ser,))
    write_thread = threading.Thread(target=serial_write, args=(ser,))

    read_thread.daemon = True  # Allow program to exit even if thread is running
    write_thread.daemon = True

    read_thread.start()
    write_thread.start()

    try:
        # Keep the main thread alive
        while run:
            time.sleep(0.1)
    finally:
        run = False
        time.sleep(0.5)
        print(f"{Fore.YELLOW}\nClosing serial port\n{Fore.RESET}")
        ser.close()
        read_thread.join()
        write_thread.join()

if __name__ == "__main__":
    main()