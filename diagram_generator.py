"""module responsible for generating traffic diagrams"""
import sys
import os
from typing import List
import matplotlib.pyplot as plt

class TrafficData:
    timestamp: float
    msg_src: str
    msg_dst: str
    msg_len: int

    def __init__(self, timestamp: float, msg_src: str, msg_dst: str, msg_len: int) -> None:
        self.timestamp = timestamp
        self.msg_len = msg_len
        self.msg_src = msg_src
        self.msg_dst = msg_dst

# seconds_dict[time_frame][link] = number of bytes sent towards link in time_frame
def sort_messages(messages : List[TrafficData]):
    links = []
    for msg in messages:
        src = msg.msg_src
        dst = msg.msg_dst
        if src > dst:
            tmp = src
            src = dst
            dst = tmp
        link = src + " <-> " + dst
        # filter flooding messages
        if not src.startswith("00:00:00:00:00") or not dst.startswith("00:00:00:00:00"):
            continue
        if not link in links:
            links.append(link)
    links.append("ALL")
    seconds_dict = {}
    total_seconds = 0.5
    seconds_dict[0.5] = {}
    for link in links:
        seconds_dict[0.5][link] = 0
    while len(messages) > 0:
        if messages[0].timestamp < total_seconds:
            src = messages[0].msg_src
            dst = messages[0].msg_dst
            # filter flooding messages
            if not src.startswith("00:00:00:00:00") or not dst.startswith("00:00:00:00:00"):
                seconds_dict[total_seconds]["ALL"] = seconds_dict[total_seconds]["ALL"] + messages[0].msg_len
                messages.pop(0)
                continue
            if src > dst:
                tmp = src
                src = dst
                dst = tmp
            link = src + " <-> " + dst
            seconds_dict[total_seconds][link] = seconds_dict[total_seconds][link] + messages[0].msg_len
            seconds_dict[total_seconds]["ALL"] = seconds_dict[total_seconds]["ALL"] + messages[0].msg_len
            messages.pop(0)
        else:
            total_seconds += 0.5
            seconds_dict[total_seconds] = {}
            for link in links:
                seconds_dict[total_seconds][link] = 0
    return links,seconds_dict

def main():
    """main"""
    # take filename from arguments
    if len(sys.argv) != 3:
        print("Usage: python diagram_generator.py <filename> <output_folder>")
        return
    filename = sys.argv[1]
    output_folder = sys.argv[2]
    messages = []
    with open(filename, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line_data = line.split(" ")
            messages.append(TrafficData(float(line_data[0]), str(line_data[1]), str(line_data[2]),int(line_data[3])))
    links,data = sort_messages(messages)
    #print(data)
    if not os.path.isdir(output_folder):
        os.mkdir(output_folder)
    for link in links:
        link_data = {}
        for time_frame in data.keys():
            link_data[time_frame] = data[time_frame][link]
        # plot data on diagram
        plt.plot(link_data.keys(), link_data.values())
        plt.xlabel('Time [s]')
        plt.ylabel('Number of messages')
        ax = plt.gca()
        ax.set_yscale('log')
        plt.title(f'Traffic diagram {link}')
        
        plt.savefig(f"{output_folder}/{link}.png")
        #plt.show()

if __name__ == '__main__':
    main()