 #!/usr/bin/python

from mininet.topo import Topo
from mininet.topolib import TreeTopo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI

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
  import time
  work_dir = ' /home/mininet/measurement-service/'
  if len(hosts) > 1:
    # fake one host as controller and send configuration messages to other hosts
    c = hosts[0]
    p = hosts[1]
    leaf = hosts[2:len(hosts)] 
    leaf_addrs = [h.IP() for h in leaf]
    
    p.cmd('python' + work_dir + 'agent.py -a ' + p.IP() + ' -l ' + '\''+str(leaf_addrs)+'\''+ ' &')
    p.cmd('python' + work_dir + 'monitor.py' + '&') 

    for h in leaf:
      h.cmd('python' + work_dir + 'agent.py -a ' + h.IP() + ' &')
      h.cmd('python' + work_dir + 'monitor.py' + ' &') 
    
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
    print 'query heavy hitter: ' + c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + p.IP() + ' -f query_heavy_hitters' )

def clear_counters(hosts):
  work_dir = ' /home/mininet/measurement-service/'
  for i,h in enumerate(hosts):
    if i > 0: 
      ip = h.IP() 
      h.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + ip + ' -f clear_counters' + '&')

def simpleTest():
  "Create and test a simple network"
#  topo = SingleSwitchTopo(n=6)
  topo = TreeTopo(depth=2,fanout=3)
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
  # Tell mininet to print useful information
  setLogLevel('info')
  simpleTest()
