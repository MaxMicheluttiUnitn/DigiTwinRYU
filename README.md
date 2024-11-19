# DigiTwinRYU

This is my project for the Softwarized and Virtualized Mobile Networks course held in the University of Trento.<br>
The objective of the project is to create a digital twin of a network, which is a digital version of the network which has the same amount of nodes and links in the same configuration as the original, and to simulate the traffic that happens on the original network on the digital twin.<br>
In this project I use mininet to simulate the original network which is controlled by a RYU controller responsible for extracting the topology and recording the traffic happening on this network. Traffic is generated thourgh ping and iperf commands that can be run through the mininet command line interface.<br>
The digital twin also runs on mininet. This limitation makes it impossible to run both the original and the twin on the same machine. However, through the use of a custom built Docker container, it is possible to run both networks at the same time and recreate traffic almost in real time.<br>
This, however, came at a cost: due to issues with python version compatibility and dependency compatibility I was unable to set up a RYU controller to record the traffic inside the container.<br>
For this reason there are 2 version of this project: 
* an asynchronous version that "replays" the network in the entirety of its lifetime on the same machine where the original network ran
* a parallel version which simulates traffic in real time, but is unable to record traffic data
Both digital twin versions use the same code inside the traffic_sim.py file, and differ only in the stopping criterion, being that the parallel version always waits for new data to simulate and must be manually stopped, while the asynchronous version terminates on its own when all messages have been simulated.

## Running the asynchronous version

To run the asynchronous version, prepare two command line interfaces (CLIs), using tmux for example. <br>
First, in one of them, start the controller with the following command

```
ryu-manager digital_twin_ryu_async.py
```

Then, start the network on the other. You can use any network of your choice, it can have both a custom topology or one of the default ones from mininet. Remember to set the controller as remote. For example:

```
sudo mn --topo linear,3 --mac --switch ovsk --controller remote 
```

The topology is computed when the first non-flooding message is sent inside the network. For example, it can be computed as soom as a ping is sent inside the network. <br>
Once the topology is computed, traffic will be recorded inside a newly built directory until the controller is stopped. The controller can be stopped with a kill signal (Ctrl + C) and it will exit gracefully.

To simulate traffic inside the network you can prompt the mininet CLI with commands such as:

```
iperf h1 h2
```
```
h2 ping h1
```

You can stop mininet with the "exit" command. <br>

Once the network and the controller are stopped, a new python file "digital_twin_network.py" should have been generated (or it should have replaced the previous file with the same name). This file contains the code that is needed to generate and run the digital twin.<br>

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

For the next steps you will need 3 CLIs available.<br>

!!! You must complete the following steps in the order that is provided, otherwise the project will not work correctly !!! <br>

On the first CLI start the container as follows:

```
docker run -it --rm --name mikimax --privileged -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix -v /lib/modules:/lib/modules maxmiki/my_mn
```

Once the container is started, you can start the routine that will wait for the necessary data to build the network:

```
python3 start_routine.py
```

On the second CLI start the parallel controller:

```
ryu-manager digital_twin_ryu_parallel.py
```

Then on the third CLI start a mininet network with a remote controller. For example:

```
sudo mn --topo single,4 --mac --switch ovsk --controller remote 
```

You can now start recording messages and compute the topology by sending a non-flooding message inside the network, for example a ping. The simplest way to do so is to send a single ping from h1 to h2 in the mininet CLI (third CLI), but you can also send more complex networking commands such as iperf:
```
h1 ping -c 1 h2
```

Now you can send messgaes in the original network and those messages will be automatically simulated on the twin. 
The delay between the original and simulated message should be around 10 seconds. <br>
You can simulate more messages on the original network by typing commands in the mininet CLI such as, for example:

```
iperf h1 h2
```
```
h2 ping h1
```

Once you are satisfied with the simulation, you can stop the original network by typing "exit" in the mininet CLI.
Both the digital twin and the controller need to be stopped with a kill signal (Ctrl + C) and they will both exit gracefully.<br>
You can stop the docker container by typing the "exit" command. remember that nothing inside the container will be saved when it is stopped! However, you can find the code of the digital twin in the "digital_twin_network_parallel.py" file since the parallel controller will also save it on the original machine. This is the exact same code that is run inside the container during parallel execution and can be re-run outside the container with a proper controller in the same way as the asynchronous replay works in order to collect data about the traffic that is replicated, with the only difference in execution being that long inactive phases will be skipped.

## Drawing traffic graphs

It is possible to draw graphs that show the amount of traffic in bits sent over the network during time.<br>

The traffic of the network can be generated as follows:
```
python3 diagram_generator.py <logging_file> <output_folder>
```
The "logging_file" is the file where traffic has been logged by the corresponfing controller.<br>
The "ouput_folder" is a folder where the graphs showing traffic across links will be saved.

## Issues

The issue regarding the traffic data recording not working when simulating parallel execution depends on a compatibility issue between python 10 and the ryu-manager. If someone was able to successfully install the ryu-manager correctly inside the container (by changing the Dockerfile), it would be possible to record traffic data by running the simple_logging_controller with ryu inside the container.<br>
Another approach that would make running the parallele version and recording traffic viable would be to run the simple_logging_controller outside the machine and communicate with the mininet network running inside the machine. However I was unable to accomplish that due to issues when sending packages to and from the machine since I was unable to successfully map ports with the -p option.