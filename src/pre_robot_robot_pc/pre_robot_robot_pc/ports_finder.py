import serial.tools.list_ports
from typing import List
def find_possible_ESP32_ports() -> List[str]:
    ports = serial.tools.list_ports.comports()
    r=[]
    for port in ports:
        if port.description=="USB Serial":
            r.append(port.device)
    return r

def find_possible_RPLidar_ports() -> List[str]:
    ports = serial.tools.list_ports.comports()
    r=[]
    for port in ports:
        if "CP2102 USB to UART Bridge Controller" in port.description:
            r.append(port.device)
    return r



if __name__=="__main__":
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"Device: {port.device}")
        print(f"  Name: {port.name}")
        print(f"  Description: {port.description}")
        print(f"  HWID: {port.hwid}")
        print(f"  VID: {port.vid}, PID: {port.pid}")
        print(f"  Serial number: {port.serial_number}")
        print("-----")