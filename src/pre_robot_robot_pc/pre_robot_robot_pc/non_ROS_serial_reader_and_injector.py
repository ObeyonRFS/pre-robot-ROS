import sys
import select
import serial
import threading
import termios
import tty

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200

def serial_reader(ser):
    """ Continuously read from serial and print """
    while True:
        data = ser.readline().decode(errors="ignore").strip()
        if data:
            print(f"\r[ESP32] {data}\n> ", end="", flush=True)

def main():
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud")

    # Start background thread for serial
    threading.Thread(target=serial_reader, args=(ser,), daemon=True).start()

    # Put terminal into raw mode (so we get chars immediately)
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    try:
        buffer = ""
        print("> ", end="", flush=True)

        while True:
            # Check if keyboard has data
            rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
            if rlist:
                ch = sys.stdin.read(1)
                if ch == "\n":  # Enter pressed → send line
                    ser.write((buffer + "\n").encode())
                    buffer = ""
                    print("> ", end="", flush=True)
                elif ch == "\x03":  # Ctrl+C
                    break
                else:
                    buffer += ch
                    print(ch, end="", flush=True)

    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        ser.close()
        print("\nSerial closed.")

if __name__ == "__main__":
    main()