import time
from socket import *
import numpy as np

'''
These functions are used for absolute lat and lon
port and my_id are according to example in https://www.tacview.net/documentation/acmi/en/

NOTE:
1. Download Tacview
2. Run several episodes and save the trajectories
3. Open the application, start listening
4. Call the `data_replay` as shown in __main__
Custom config:
- PORT, default=21567
- password, default='f16sim'
'''

class TacviewClient:
    def __init__(self):
        HOST = ''
        PORT = 21567
        ADDR = (HOST, PORT)

        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.bind(ADDR)
        self.server_socket.listen(10) # max 10 tacview client

        print('waiting for connection to Tacview...')
        self.socket, address = self.server_socket.accept() # client socket
        print('...connected from: ', address)

    def init_tcp(self, password='f16sim', reference_time='2020-04-01T00:00:00Z'):
        BUFSIZE = 1024
        # handshake info
        self.socket.send(bytes('XtraLib.Stream.0\n', 'utf-8'))
        self.socket.send(bytes('Tacview.RealTimeTelemetry.0\n', 'utf-8'))
        self.socket.send(bytes('F16\n', 'utf-8'))
        self.socket.send(bytes(password+'\0', 'utf-8'))

        # print received data
        data = str(self.socket.recv(BUFSIZE), encoding='utf-8')
        try:
            data
        except NameError:
            print("no data received")
        else:
            print(data)

        # begin sending with acmi headers
        self.socket.send(bytes('FileType=text/acmi/tacview\n', 'utf-8'))
        self.socket.send(bytes('FileVersion=2.1\n', 'utf-8'))
        self.socket.send(bytes('0,ReferenceTime='+reference_time+'\n', 'utf-8'))


    def send(self, time, state_in, my_id='3000102', name='F16', color='Blue'):
        """
        Args:
            time(float): second, max precision: 0.001s (recommend 0.01s/frame)
            state_in(list): [lon, lat, alt, roll, pitch, yaw]
                lon/lat: degree, max precision: 0.0000001 degree
                alt: meter, max precision: 0.01m
                roll/pitch/yaw: degree, max precision: 0.1 degree
            color(str): 'Red' or 'Blue', distinguish different sides
        NOTE:
            roll: left roll = negative
            pitch: up head = positive
            yaw: north=0, left(anti-clockwise) = negative
        """
        state_in = np.resize(state_in,(6,))
        [lon, lat, alt, roll, pitch, yaw] = state_in

        # send relative time
        self.socket.send(bytes('#' + str(time) + '\n', 'utf-8'))

        # send flight state
        send_str = my_id + ',T=' + str(lon) + '|' + str(lat) + '|' + str(alt) + '|' \
                                 + str(roll) +'|' + str(pitch) +'|' + str(yaw) + ',Name=' + str(name) + ',Color=' + str(color) + '\n'
        self.socket.send(bytes(send_str, 'utf-8'))

    def close(self):
        self.socket.close()
        self.server_socket.close()


def show_tacview(display: TacviewClient, sim_time, state, my_id='3000001', name='F16', color='Blue'):
    display.send(time=sim_time,
                 state_in=[state[0],                    # lon, unit: degree
                           state[1],                    # lat, unit: degree
                           state[2] / 3.2808399,        # alt, unit: feet => meter
                           state[3] * 180 / np.pi,      # roll, unit: rad => degree
                           state[4] * 180 / np.pi,      # yaw, unit: rad => degree
                           state[5] * 180 / np.pi],     # pitch, unit: rad => degree
                 my_id=my_id, name=name, color=color)


def data_replay(data):
    display = TacviewClient()
    display.init_tcp()
    for time_step in range(len(data)):
        time.sleep(0.07)
        show_tacview(display, sim_time=time_step / 12, state=data[time_step][:6], my_id='3000001', name='F16', color='Blue')
        show_tacview(display, sim_time=time_step / 12, state=data[time_step][6:], my_id='3000002', name='F16', color='Red')
    display.close()


if __name__ == '__main__':
    data = np.load('save_trajectories.npy')
    data_replay(data)