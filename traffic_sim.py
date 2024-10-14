"""module to simulate traffic in the twin network"""
import time
import signal
import os
from typing import List
from collections import deque
from mininet.net import Mininet

class GracefulKiller:
    """class to handle graceful exit"""
    kill_now : bool

    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        """exit gracefully"""
        self.kill_now = True

FRAME_TIME_LENGTH = 10

class Packet:
    """class to represent a packet in the network"""
    def __init__(self,time_gap: float, source: str, destination: str, size: int) -> None:
        self.source = source
        self.destination = destination
        self.time_gap = time_gap
        self.size = size

    def __str__(self) -> str:
        return f"Packet: {self.source} -> {self.destination} at {self.time_gap} size {self.size}"

    def __repr__(self) -> str:
        return f"Packet: {self.source} -> {self.destination} at {self.time_gap} size {self.size}"

def _read_packet(input_string: str) -> Packet:
    """read packet from string"""
    data = input_string.split(" ")
    if len(data) != 4:
        raise ValueError("Invalid packet data")
    return Packet(float(data[0]), data[1], data[2], int(data[3]))

def _load_traffic_data(frame: int) -> List[Packet]:
    """load traffic data from file"""
    traffic_data = []
    with open(f"traffic/{frame}.txt", "r", encoding='utf8') as file:
        for line in file:
            traffic_data.append(_read_packet(line))
    return traffic_data

def _current_frame_has_data(frame: int) -> bool:
    """check if current frame has data"""
    return os.path.isfile(f"traffic/{frame}.txt")

def _simulate_packets(network: Mininet,packets: List[Packet], is_parallel_simulation: bool) -> None:
    """simulate packet in the network"""
    #print(f"Packet: {packet.source} -> {packet.destination} at {packet.time_gap}")
    send_counter = {}
    for packet in packets:
        if packet.source not in send_counter:
            send_counter[packet.source] = {}
        if packet.destination not in send_counter[packet.source]:
            send_counter[packet.source][packet.destination] = 0
        send_counter[packet.source][packet.destination] += packet.size
    for source in send_counter.keys():
        src_host = network.get(source)
        for destination in send_counter[source].keys():
            result = src_host.cmd(f"ping -q -c 1 -s {max(28,send_counter[source][destination])} 10.0.0.{destination.replace('h','')}")
            if is_parallel_simulation:
                print(result)

def simulate_traffic(network: Mininet, is_parallel_simulation: bool) -> None:
    """reproduces traffic in the network"""
    # check if traffic directory is available
    if not os.path.isdir("traffic"):
        print("Traffic directory not found...")
        return
    # check if traffic directory is empty
    if not is_parallel_simulation:
        if not os.listdir("traffic"):
            print("No traffic data found...")
            return
    else:
        while not os.listdir("traffic"):
            time.sleep(1)
    #time.sleep(5)
    current_frame = 0
    if not _current_frame_has_data(current_frame):
        return
    frame_start_time = time.time()
    loaded_data : deque[Packet] = deque(_load_traffic_data(current_frame))
    killer = GracefulKiller()
    while not killer.kill_now:
        current_time = time.time()
        elapsed_time = current_time - frame_start_time
        packets_to_sim = []
        while len(loaded_data) > 0 and elapsed_time > loaded_data[0].time_gap:
            packets_to_sim.append(loaded_data.popleft())
        _simulate_packets(network,packets_to_sim, is_parallel_simulation)
        if elapsed_time > FRAME_TIME_LENGTH:
            if not _current_frame_has_data(current_frame + 1):
                if is_parallel_simulation:
                    # sleep half a frame and check again
                    time.sleep(FRAME_TIME_LENGTH // 2)
                else:
                    return
            else:
                current_frame += 1
                frame_start_time = current_time
                loaded_data = deque(_load_traffic_data(current_frame))
        time.sleep(0.01)

# if __name__ == "__main__":
#     simulate_traffic()
