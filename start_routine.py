import time
import os

def main():
    counter = 0
    print("Waiting for network to be available...")
    while True:
        if os.path.isfile("network.py"):
            break
        time.sleep(1)
        # every 10 seconds print a message to signal that the network is not available yet
        if counter > 0 and counter % 10 == 0:
            print("Waiting for network to be available...")
        counter += 1
    # load and run network
    import network
    network.main()

if __name__ == "__main__":
    main()