 #!/usr/bin/python

from mininet.topo import Topo
from mininet.topolib import TreeTopo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI

import pprint, requests

class CircleSwitchTopo(Topo):
  "switches connected into circle."
  def build(self, n=3, m=3):
    switch_list = []
    for s in range(m):
      switch = self.addSwitch('s%s' % (s+1))
      switch_list.append(switch)
      if s > 0:
        self.addLink(switch,switch_list[s-1])
      if s == m-1:
        self.addLink(switch,switch_list[0])
    # Python's range(N) generates 0..N-1
    for h in range(n):
      host = self.addHost('h%s' % (h + 1))
      self.addLink(host, switch_list[h%m])

class SingleSwitchTopo(Topo):
  "Single switch connected to n hosts."
  def build(self, n=2):
    switch = self.addSwitch('s1')
    # Python's range(N) generates 0..N-1
    for h in range(n):
      host = self.addHost('h%s' % (h + 1))
      self.addLink(host, switch)

# run monitor and agent on each hosts
def config_hosts(hosts):
  work_dir = ' /home/mininet/measurement-service/'

  # start agent and monitor
  for h in hosts:
    h.cmd('python' + work_dir + 'agent.py -a ' + h.IP() + ' &')
    h.cmd('python' + work_dir + 'monitor.py' + ' &') 

def setup_tree_overlay(hosts, depth, fan):
  import time,math
  work_dir = ' /home/mininet/measurement-service/'
  # configure virtual overlay   
  for i,h in enumerate(hosts):
    for d in range(depth):
      if i % int(math.pow(fan,d+1)) == 0:
        for f in range(fan-1):
          leaf_id = i + int(math.pow(fan,d)) * (f+1)
          h.cmd('python' + work_dir + 'tests/add_leaf.py -f add' + ' -r ' + h.IP() + ' -l ' + hosts[leaf_id].IP() )
    # print 'leaf node of h' + str(i+1)
    # print h.cmd('python' + work_dir + 'tests/add_leaf.py -f display' + ' -r ' + h.IP() )

def setup_without_overlay(hosts):
  work_dir = ' /home/mininet/measurement-service/'
  r = hosts[0]
  for i,h in enumerate(hosts):
    if i > 0:
      r.cmd('python' + work_dir + 'tests/add_leaf.py -f add' + ' -r ' + r.IP() + ' -l ' + h.IP() )
  # print 'leaf nodes of h1'
  # print r.cmd('python' + work_dir + 'tests/add_leaf.py -f display' + ' -r ' + r.IP() )

def config_counters(hosts):
  work_dir = ' /home/mininet/measurement-service/'
  # configure counters and sketches on hosts
  c = hosts[1]
  r = hosts[0]
  c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + r.IP() + ' -f config_counters') 
  c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + r.IP() + ' -f config_sketch') 

# send messages to do measurements
def send_msg(hosts):
  work_dir = ' /home/mininet/measurement-service/'
  if len(hosts) > 1:
    # fake one host as controller and send configuration messages to other hosts
    c = hosts[1]
    p = hosts[0]
    ip = p.IP() 
    print 'query counters: ' + c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + p.IP() + ' -f query_counters')
    print 'query sketch: ' + c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + p.IP() + ' -f query_sketch') 
    print 'query heavy hitter: ' 
    print c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + p.IP() + ' -f query_heavy_hitters' )

def clear_counters(hosts):
  work_dir = ' /home/mininet/measurement-service/'
  for i,h in enumerate(hosts):
    ip = h.IP() 
    h.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + ip + ' -f clear_counters' + '&')

def simpleTest(depth,fanout):
  "Create and test a simple network"
#  topo = SingleSwitchTopo(n=6)
  topo = TreeTopo(depth=depth,fanout=fanout)
  net = Mininet(topo)
  net.start()
  print "Dumping host connections"
  dumpNodeConnections(net.hosts)
  dumpNodeConnections(net.switches)
  print "Testing measurement service"
  
  # configure for monitoring
  config_hosts(net.hosts)
  setup_without_overlay(net.hosts)
  # setup_tree_overlay(net.hosts, depth, fanout)
  config_counters(net.hosts)
  send_msg(net.hosts)
  clear_counters(net.hosts)
  CLI(net)
  net.stop()

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='This is SoNIC server')
  parser.add_argument('-f','--fanout',help='fanout of tree topology',default=3)
  parser.add_argument('-d','--depth',help='depth of tree topology',default=2)
  args = parser.parse_args()
  # Tell mininet to print useful information
  setLogLevel('info')
  simpleTest(int(args.depth),int(args.fanout))
