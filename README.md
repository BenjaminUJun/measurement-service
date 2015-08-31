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

## Basic Example: Query Available Bandwidth
Let's first create a file with the following lines of codes.

```
import requests
# request available bandwidth with JSON message
data = {'type' : 'query bw',\
'src' : '10.0.0.5',\
'dst' : '10.0.0.6'}

# tells src host to start bandwidth estimation
# agent listens on port 8000
url = 'http://10.0.0.5:8000'

r = requests.post(url,data=data)
# src host response with available bandwidth in MBytes/s
print r.text + ' MBytes/s'
```
The file has been saved at ``examples/query_bw.py``. Let's start a simulation environment with mininet.
```
sudo python mt.py
```

run the query codes on h1
```
mininet> h1 python examples/query_bw.py
```
and you get the available bandwidth from h5 to h6
```
1980MBytes/s
```


## Example with distribution data: Heavy Hitter Monitoring

To monitor the heavy hitter of a certain host, we need to configure counters to collect distribution data. let's first create a file with these few lines of codes.

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

The file has been saved in ``examples/heavy_hitter.py``. Then start the simulatioin environment:

```
sudo python mt.py
```

This script starts a network in tree topology with 9 host (depth=2, fan=3), and automatically starts agent and monitor programs on h2-h9, leaving h1 acts as a controller outside the monitored network. Now you should see Mininet's command line interface.

Run your heavy hitter monitoring program on h1:

```
mininet> h1 python examples/heavy_hitter.py &
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

## Globa monitoring example: flow size distribution monitor

To do this, first create a file with the following cotnets:
```
import requests, json, time, ast
# targeted end-host is root node: h2
addr = "10.0.0.2"
# agent programs listen on port 8000
port = 8000

# --------------------------
# Configuration
# This is an example that monitors the global traffic
# --------------------------

# a json message: to apply filter rules on targeted end-host
# for the convenicence of packet generation within mininet, just filter the icmp pakcets
data = {'type':  'config sketch', \
'interface': 'INPUT', \
'proto' : 'icmp'}
url = 'http://' + addr + ':' + str(port)
r = requests.post(url,data=data)

# Targeted end-hosts response with the sketch id
sketch_id = int(r.text)

# message to configure counter on the sketch
# flow size distribution: collect the distribution among different <src,dst> combinations
data = {'type': 'config sketch counter',\
'sketch_id': sketch_id,\
'counter_key_type': 'src_dst',\
'increment': 'bytes'}
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
'counter_key_type': 'src_dst'}
  # targetted end-host response with the heavy hitter records in JSON message
  r = requests.post(url,data=data)
  # parse text to json message
  d = ast.literal_eval(r.text)
  print json.dumps(d,sort_keys=True,indent=4)
  
  # query one counter entry by key
  data={'type': 'query sketch', \
'sketch_id': sketch_id, \
'counter_key_type': 'src_dst',\
'counter_key': '10.0.0.6,10.0.0.5'}
  # targetted end-host response with the value
  r = requests.post(url,data=data)
  print 'h6 hits h5: ' +  r.text + 'times'
```

The scripts have been saved in ``examples/flow_size_distrib.py``. Then start the simulatioin environment:

```
sudo python mt.py
```

This script starts a network in tree topology with 9 host (depth=2, fan=3), and automatically starts agent and monitor programs on h2-h9, leaving h1 acts as a controller outside the monitored network. Now you should see Mininet's command line interface.

Run your heavy hitter monitoring program on h1:

```
mininet> h1 python examples/flow_size_distrib.py &
```

Generate some icmp traffic with 
```
mininet> pingall
```

Watch the output of the flow size distribution monitoring program

```
mininet> h1 jobs
{
    "10.0.0.1,10.0.0.6": 2, 
    "10.0.0.1,10.0.0.7": 2, 
    "10.0.0.1,10.0.0.8": 2, 
    "10.0.0.1,10.0.0.9": 2, 
    "10.0.0.2,10.0.0.5": 2, 
...
}
h6 hits h5: 2times
```

## Example with real time counter: Portscan Detection

For real time measurement tasks, the system provides real time counters to monitor real time traffic of the network

To do this, we still first create a file

```
import requests, json, time, ast, re, collections
# targeted end-host is h5
addr = "10.0.0.5"
# agent programs listen on port 8000
port = 8000

# --------------------------
# Configuration
# --------------------------

# a json message: to apply filter rules on targeted end-host
data = {'type':  'config sketch', \
'interface': 'INPUT'}
url = 'http://' + addr + ':' + str(port)
r = requests.post(url,data=data)

# Targeted end-hosts response with the sketch id
sketch_id = int(r.text)

# message to configure counter on the sketch
data = {'type': 'config sketch counter',\
'sketch_id': sketch_id,\
'counter_key_type': 'src_dport',\
'increment': 'pkt'}
r = requests.post(url,data=data)

# configure anothe counter to collect distribution data among dports
data = {'type': 'config sketch counter',\
'sketch_id': sketch_id,\
'counter_key_type': 'dport',\
'increment': 'pkt'}
r = requests.post(url,data=data)

# ---------------------------
# Query Counters periodically
# ---------------------------

key_num = 0
new_key_num = 0

while True:
  # for portscan detection, query interval should be shorter: 300ms
  time.sleep(0.3)

  # query how many disdinct keys are in the real time counter
  # to detect a burst in port access
  data={'type': 'query sketch', \
'sketch_id': sketch_id, \
'counter_key_type': 'dport',\
'counter_key': 'real_time_key_num'}
  # targetted end-host response with the number of disdinct keys in the real time counter
  r = requests.post(url,data=data)
  # use status code to guarantee a correct response. 200 for correct.
  if r.status_code == 200:
    key_num = new_key_num  
    new_key_num = int(r.text)
  # if the number of distinct requested port increased more than 20 in a single interval, a port scan is detected
  if new_key_num - key_num > 20:
    print 'portscan detected.'
    # query the real time traffic distribution among distinct <src addr, dst port> combination
    data={'type': 'query real time counter', \
'sketch_id': sketch_id, \
'counter_key_type': 'src_dport'}
    r = requests.post(url,data=data)
    if r.status_code == 200:
      ip_list = re.findall('\d+\.\d+\.\d+\.\d+',r.text)
      freq = collections.Counter(ip_list)
      print json.dumps(dict(freq),sort_keys=True,indent=4)
```

The scripts have been saved in ``examples/portscan.py``. Then start the simulatioin environment:

```
sudo python mt.py
```

This script starts a network in tree topology with 9 host (depth=2, fan=3), and automatically starts agent and monitor programs on h2-h9, leaving h1 acts as a controller outside the monitored network. Now you should see Mininet's command line interface.

Run your heavy hitter monitoring program on h1:

```
mininet> h1 python examples/portscan.py &
```

Do portscan with net cat
```
mininet> h6 nc -z 10.0.0.5 8008-8092
```

Watch the output of the portscan detection program

```
mininet> h1 jobs
portscan detected.
{
    "10.0.0.1": 1, 
    "10.0.0.6": 85
}
```
The result shows that 10.0.0.6 requests on 85 disdinct port in an detection interval (here is 300ms)
