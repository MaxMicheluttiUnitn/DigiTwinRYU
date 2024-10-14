# DigiTwinRYU

This is my project for the Softwarized and Virtualized Mobile Networks course held in the University of Trento.
The objective of the project is to create a digital twin of a network, which is a digital version of the network which has the same amount of nodes and links in the same configuration as the original, and to simulate the traffic that happens on the original network on the digital twin.
In this project I use mininet to simulate the original network which is controlled by a RYU controller responsible for extracting the topology and recording the traffic happening on this network. Traffic is generated thourgh ping and iperf commands that can be run through the mininet command line interface.
The digital twin also runs on mininet. This limitation makes it impossible to run both the original and the twin on the same machine. However, through the use of a custom built Docker container, it is possible to run both networks at the same time and recreate traffic almost in real time.
This, however, came at a cost: due to issues with python version compatibility and dependency compatibility I was unable to set up a RYU controller to record the traffic inside the container.
For this reason there are 2 version of this project: 
* an asynchronous version that "replays" the network in the entirety of its lifetime on the same machine where the original network ran
* a parallel version which simulates traffic in real time, but is unable to record traffic data
Both digital twin versions use the same code inside the traffic_sim.py file, and differ only in the stopping criterion, being that the parallel version always waits for new data to simulate and must be manually stopped, while the asynchronous version terminates on its own when all messages have been simulated.

## Running the asynchronous version

To run the asynchronous version, prepare two command line interfaces (CLIs), using tmux for example. 
First, in one of them, start the controller with the following command

```
ryu-manager digital_twin_ryu_async.py
```

Then, start the network on the other. You can use any network of your choice, it can have both a custom topology or one of the default ones from mininet. Remember to set the controller as remote. For example:

```
sudo mn --topo linear,3 --mac --switch ovsk --controller remote 
```

The topology is computed when the first non-flooding message is sent inside the network. For example, it can be computed as soom as a ping is sent inside the network. 
Once the topology is computed, traffic will be recorded inside a newly built directory until the controller is stopped. The controller can be stopped with a kill signal (Ctrl + C) and it will exit gracefully.

To simulate traffic inside the network you can prompt the mininet CLI with commands such as:

```
iperf h1 h2
```
```
h2 ping h1
```

You can stop mininet with the "exit" command.

Once the network and the controller are stopped, a new python file "digital_twin_network.py" should have been generated (or it should have replaced the previous file with the same name). This file contains the code that is needed to generate and run the digital twin.

Once again, using two CLIs, start the controller for the twin. In this case you only need a simple controller that will only observe the traffic and tell the switches to forward messages. To run this controller type:

```
ryu-manager simple_logging_controller.py
```

Then you can start the digital twin network which will recreate the topology and traffic from the original network. To do so, type this command on the other CLI:

```
sudo python3 digital_twin_network.py
```

This network will automatically stop once all traffic has been simulated, while the controller needs to be stopped manually.

## Running the parallel version

To run this version of the code first you need to build the docker image that will host the digital twin mininet network. This can be done in one line of code as follows:

```
docker build -t maxmiki/my_mn .
```

Once the image is built it should appear inside the list of available images. You can check if everything went correctly by typing the following command and looking for the maxmiki/my_mn image:

```
docker images
```

For the next steps you will need 3 CLIs available.

!!! You must complete the following steps in the order that is provided, otherwise the project will not work correctly !!!

On the first CLI start the container as follows:

```
docker run -it --rm --name mikimax --privileged -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v /lib/modules:/lib/modules maxmiki/my_mn
```

On the second CLI start the parallel controller:

```
ryu-manager digital_twin_ryu_parallel.py
```

Then om the third CLI start a mininet network with a remote controller. For example:

```
sudo mn --topo star,4 --mac --switch ovsk --controller remote 
```

You can now start recording messages and compute the topology by sending a non-flooding message inside the network, for example a ping. I suggest to send a single simple message since this operation will not start the twin automatically, but will generate the twin code that we can start inside the container. The simplest way to do so is to send a single ping from h1 to h2 in the mininet CLI (third CLI):
```
h1 ping -c 1 h2
```
This is not necessary and all traffic sent before the start of the twin will be eventually simulated on the twin, however starting the twin as soon as possible will decrease drastically the delay between the original and simulated messages.

Now you can start the parallel twin network. In the first CLI where the container runs type the following command:
```
python3 network.py
```
You do not need to use sudo since all commands that run in docker containers are run as super-user by default.

Now you can send messgaes in the original network and those messages will be automatically simulated on the twin. 
The delay between the original and simulated message should be around 10 seconds, if the digital twin is not busy simulating old messages. 
When the original network is inactive, nothing will be simulated and as soon as the original network gets active again, the twin resumes simulating messages. This allows the twin to catch up to the original network if it is inactive for some time.
You can simulate messages on the original network by typing commands in the mininet CLI such as:

```
iperf h1 h2
```
```
h2 ping h1
```

Once you are satisfied with the simulation, you can stop the original network by typing "exit" in the mininet CLI.
Both the digital twin and the controller need to be stopped with a kill signal (Ctrl + C) and they will both exit gracefully.
You can stop the docker container by typing the "exit" command. Nothing inside the container will be saved. However, you can find the code of the digital twin in the "network.py" file since the parallel controller will also save it on the original machine. This is the exact same code that is run in the container during parallel execution and can be re-run outside the container with a proper controller in the same way as the asynchronous replay works to collect data about the traffic that is replicated, with the only difference in execution being that long inactive phases will be skipped.

## Drawing traffic graphs

It is possible to draw graphs that show the amount of traffic in bits sent over the network during time.

The traffic of the original network can be observed by typing (after the controller has been stopped):
```
python3 msg_count.txt
```

The traffic of the digital twin network can be observed by typing (after the controller has been stopped):
```
python3 msg_count_twin.txt
```