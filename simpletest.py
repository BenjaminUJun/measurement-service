 #!/usr/bin/python

from mininet.topo import Topo
from mininet.topolib import TreeTopo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI

import pprint

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
  import time
  work_dir = ' /home/mininet/measurement-service/'
  n = len(hosts)
  if n > 3:
    # fake one host as controller and send configuration messages to other hosts
    c = hosts[0]
    p = hosts[1]
    leaf = hosts[2:4] 
    leaf_addrs = [h.IP() for h in leaf]
    
    p.cmd('python' + work_dir + 'agent.py -a ' + p.IP() + ' -l ' + '\''+str(leaf_addrs)+'\''+ ' &')

    if n > 5:
      p1 = hosts[2]
      leaf = hosts[4:2+n/2] 
      leaf_addrs = [h.IP() for h in leaf]
      p1.cmd('python' + work_dir + 'agent.py -a ' + p1.IP() + ' -l ' + '\''+str(leaf_addrs)+'\''+ ' &')
      p1 = hosts[3]
      leaf = hosts[2+n/2:n] 
      leaf_addrs = [h.IP() for h in leaf]
      p1.cmd('python' + work_dir + 'agent.py -a ' + p1.IP() + ' -l ' + '\''+str(leaf_addrs)+'\''+ ' &')

    for i,h in enumerate(hosts):
      if i > 3: 
        h.cmd('python' + work_dir + 'agent.py -a ' + h.IP() + ' &')
      if i > 0:
        h.cmd('python' + work_dir + 'monitor.py' + ' &') 
        h.cmd('~/ditg/bin/ITGRecv &')
    
    # configure counters and sketches on hosts
    time.sleep(0.5)
    c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + p.IP() + ' -f config_counters') 
    c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + p.IP() + ' -f config_sketch') 

# send messages to do measurements
def send_msg(hosts):
  work_dir = ' /home/mininet/measurement-service/'
  if len(hosts) > 1:
    # fake one host as controller and send configuration messages to other hosts
    c = hosts[0]
    p = hosts[1]
    ip = p.IP() 
    print 'query counters: ' + c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + p.IP() + ' -f query_counters')
    print 'query sketch: ' + c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + p.IP() + ' -f query_sketch') 
    print 'query heavy hitter: ' 
    print c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + p.IP() + ' -f query_heavy_hitters' )

def clear_counters(hosts):
  work_dir = ' /home/mininet/measurement-service/'
  for i,h in enumerate(hosts):
    if i > 0: 
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
  print "Testing network connectivity"
  net.pingAll()
  print "Testing measurement service"
  config_hosts(net.hosts)
  net.pingAll()
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
