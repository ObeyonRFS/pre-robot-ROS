from rplidar import RPLidar

PORT_NAME = '/dev/ttyUSB1'  # your lidar port

def main():
    lidar = RPLidar(PORT_NAME)

    try:
        print("Starting scan... Press Ctrl+C to stop")
        for scan in lidar.iter_scans():  # yields lists of (quality, angle, distance)
            for (_, angle, distance) in scan:
                print(f"Angle: {angle:.2f}°, Distance: {distance} mm")
    except KeyboardInterrupt:
        print("Stopping.")
    finally:
        lidar.stop()
        lidar.disconnect()

if __name__ == '__main__':
    main()
