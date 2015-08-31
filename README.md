# An End-host based Network Measurement Service

This system provides flexible APIs to do network measurement tasks. APIs are provided in JSON messages. Network manager sends JSON messages to an root end-hosts to configure measurement tasks and query statistics.

The following example will show how to use the APIs to do heavy hitter detection, bandwidth estimation and portscan detection.

## How it works

#### Monitoring Traffic on End-hosts

This is an end-host based system. To let it work, measurement programs should be running on **each end-hosts** within the network you want to monitor. There are two programs need to run on each end-host, an agent program(agent.py) and a monitor program(monitor.py).

The agent program is responsible to communicate with each end-hosts. More concretely, it listens and responses to query messages from user, and then configure the monitor program to do coresponding measurement tasks.

The monitor program is responsible to do measurement tasks. 

#### Virtua Overlay to Integrate Statistics for Global Measurement Tasks

In global measurement tasks, agents on end-hosts integrate their statistics on a virtual overlay . The point is to save the integration work for the controller. The controller only needs to interact with the root node of the virtual overlay to do global measurement tasks.

## Installation

some python libs need to be installed to support the system functionality

install python development files

```
apt-get install build-essential python-dev libnetfilter-queue-dev
```

install Netfilter Queue python lib

```
pip install NetfilterQueue
```

install count-min sketch python lib

```
pip install madoka
```
## Example: Heavy Hitter Monitoring

```
import requests, json, time, ast
# targeted end-host is h5
addr = "10.0.0.5"
# agent programs listen on port 8000
port = 8000

# --------------------------
# Configuration
# --------------------------

# a json message: to apply filter rules on targeted end-host
data = {'type':  'config sketch', \
'interface': 'INPUT', \
'proto' : 'icmp'}
url = 'http://' + addr + ':' + str(port)
r = requests.post(url,data=data)

# Targeted end-hosts response with the sketch id
sketch_id = int(r.text)

# message to configure counter on the sketch
data = {'type': 'config sketch counter',\
'sketch_id': sketch_id,\
'counter_key_type': 'src',\
'increment': 'pkt'}
r = requests.post(url,data=data)

# ---------------------------
# Query Counters periodically
# ---------------------------

while True:
  # query counters every 5 seconds
  time.sleep(5)

  # query heavy hitter from the counter
  data={'type': 'query heavy hitters', \
'sketch_id': sketch_id, \
'counter_key_type': 'src'}
  # targetted end-host response with the heavy hitter records in JSON message
  r = requests.post(url,data=data)
  # parse text to json message
  d = ast.literal_eval(r.text)
  print json.dumps(d,sort_keys=True,indent=4)
  
  # query one counter entry by key
  data={'type': 'query sketch', \
'sketch_id': sketch_id, \
'counter_key_type': 'src',\
'counter_key': '10.0.0.6'}
  # targetted end-host response with the value
  r = requests.post(url,data=data)
  print 'h6 hits: ' +  r.text + 'times'
```

The scripts have been saved in ``simeple_examples/heavy_hitter.py``. Then start the simulatioin environment:

```
sudo python mt.py
```

This script starts a network in tree topology with 9 host (depth=2, fan=3), and automatically starts agent and monitor programs on h2-h9, leaving h1 acts as a controller outside the monitored network. Now you should see Mininet's command line interface.

Run your heavy hitter monitoring program on h1:

```
mininet> h1 python simple_examples/heavy_hitter.py &
```

Generate some icmp traffic with 
```
mininet> pingall
```

Watch the output of the heavy hitter monitoring program
```
mininet> h1 jobs
{
    "10.0.0.2": 2, 
    "10.0.0.3": 2, 
    "10.0.0.4": 2, 
    "10.0.0.6": 2, 
    "10.0.0.7": 2, 
    "10.0.0.8": 2, 
    "10.0.0.9": 2
}
h6 hits: 2times
```

* "interface": specifies which interface to monitor, INPUT or OUTPUT
* "type": purpose of the message
* "proto": the protocol used, including udp, tcp, icmp.

* "sketch\_id": specifies which sketch on the receiving host is to be configured.
* "counter\_key\_type": configures what type of key the counter will use. Here with the value "src\_dst", the monitor on h2 will create a counter that learns the srouce address and destination address information from the input packets and use the combination of < source addr , destination addr > as the counter key.
* "increment": configures the increment of each counter entry. "bytes" tells the monitor on h2 to learn the byte number of each input packet and add it to the coresponding entry.

## More complicated example: Portscan Detection

#### STEP2: Configure counters

```
mininet> h1 python examples/port_scan.py -a 10.0.0.7 -f config_sketch
sketch id: 1
{'type': 'config sketch counter', 'sketch_id': u'1', 'counter_key_type': 'src_dport'}
200
{'type': 'config sketch counter', 'sketch_id': u'1', 'counter_key_type': 'dport'}
200
```

This command let h1 sends configuration message to h7, which tells h7 to initialize necessary counters.

Agent on h7 response with the id of counter (the sketch id: 1).

#### STEP3: Generate traffic (or in real network: wait and see what it counts)

```

```
