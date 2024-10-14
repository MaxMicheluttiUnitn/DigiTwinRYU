"""module responsible for generating traffic diagrams"""
import sys
from typing import List
import matplotlib.pyplot as plt

class TrafficData:
    timestamp: float
    msg_len: int

    def __init__(self, timestamp: float, msg_len: int) -> None:
        self.timestamp = timestamp
        self.msg_len = msg_len

def sort_messages(messages : List[TrafficData]):
    seconds_dict = {}
    total_seconds = 0.5
    seconds_dict[0.5] = 0
    while len(messages) > 0:
        if messages[0].timestamp < total_seconds:
            seconds_dict[total_seconds] = seconds_dict[total_seconds] + messages[0].msg_len
            messages.pop(0)
        else:
            total_seconds += 0.5
            seconds_dict[total_seconds] = 0
    return seconds_dict

def main():
    """main"""
    # take filename from arguments
    if len(sys.argv) != 2:
        print("Usage: python diagram_generator.py <filename>")
        return
    filename = sys.argv[1]
    messages = []
    with open(filename, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line_data = line.split(" ")
            messages.append(TrafficData(float(line_data[0]), int(line_data[1])))
    data = sort_messages(messages)
    print(data)
    # plot data on diagram
    plt.plot(data.keys(), data.values())
    plt.xlabel('Time [s]')
    plt.ylabel('Number of messages')
    ax = plt.gca()
    ax.set_yscale('log')
    plt.title('Traffic diagram')
    plt.show()

if __name__ == '__main__':
    main()