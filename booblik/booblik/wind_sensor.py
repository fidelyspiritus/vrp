import rclpy
from rclpy.node import Node
from std_msgs.msg import UInt8MultiArray
from threading import Thread
import time
import libscrc
import struct


class WindSensor(Node):
    sensor_idx = 0x3
    rqst_msg = [sensor_idx, 0x03, 0x00, 0x00, 0x00, 0x09, 0xFF, 0xFF]


    def __init__(self):
        super().__init__('wind_sensor')
        self.tx_ = self.create_publisher(
            UInt8MultiArray,
            '/booblik/rs485Rx',
            10
        )
        self.rx_ = self.create_subscription(
            UInt8MultiArray,
            '/booblik/rs485Tx',
            self.recieve_callback,
            10
        )
        self.sendThread = Thread(
            target=self.request_thread, daemon=True).start()


    def check_crc (self, data):
        size = len(data)
        if (size < 3):
            return False
        
        crc = libscrc.modbus(bytes(data[0:(size - 2)]))
        crcLow = crc & 0xFF
        crcHigh = crc >> 8
        if (crcLow == data[size - 2]) and (crcHigh == data[size - 1]):
            return True
        else:
            return False


    def check_idx (self, data):
        if data[0] == self.sensor_idx:
            return True
        else:
            return False


    def parce_msg (self, data):
        speed_array = bytes([data[9],data[10],data[7],data[8]])
        try:
            derectionDegree = struct.unpack(">H", data[5:7])[0]
            speedMeterPerSecond = struct.unpack(">f", speed_array[0:4])[0]
            return (derectionDegree, speedMeterPerSecond)
        except:
            print("Parce error")
            return (0.0, 0.0)


    def recieve_callback(self, msg):
        data = msg.data

        if self.check_crc(data) == False:
            print("Crc parse error")
            return

        if self.check_idx(data) == False:
            return
        
        print(self.parce_msg(data))


    def get_rqst_msg (self):
        l = self.rqst_msg
        crc = libscrc.modbus(bytes(l[0:6]))
        crcLow = crc & 0xFF
        crcHigh = crc >> 8
        l[6] = crcLow
        l[7] = crcHigh
        return l


    def request_thread (self):
        while True:
            request_message = self.get_rqst_msg()
            self.send_message(request_message)
            time.sleep(1)

    
    def send_message(self, message):
        try:
            msg = UInt8MultiArray()

            for item in message:
                msg.data.append(item)
            
            self.tx_.publish(msg)
        except Exception as e:
            print("Error send message:", e)


def main(args=None):
    rclpy.init(args=args)
    wind_sensor = WindSensor()
    rclpy.spin(wind_sensor)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
