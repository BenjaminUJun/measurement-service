 #!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI

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
  for h in hosts:
    ip = h.IP()  
    h.cmd('python' + work_dir + 'agent.py -a ' + ip + ' &')
    h.cmd('python' + work_dir + 'monitor.py' + ' &') 

# send messages to do measurements
def send_msg(hosts):
  import requests
  work_dir = ' /home/mininet/measurement-service/'
  if len(hosts) > 1:
    h1 = hosts[0]
  for h in hosts:
    ip = h.IP() 
    print h.cmd('python' + work_dir + 'test.py -a ' + ip)

def simpleTest():
  "Create and test a simple network"
  topo = SingleSwitchTopo(n=4)
  net = Mininet(topo)
  net.start()
  print "Dumping host connections"
  dumpNodeConnections(net.hosts)
  print "Testing network connectivity"
  net.pingAll()
  print "Testing measurement service"
  config_hosts(net.hosts)
  send_msg(net.hosts)
  CLI(net)
  net.stop()

if __name__ == '__main__':
  # Tell mininet to print useful information
  setLogLevel('info')
  simpleTest()
