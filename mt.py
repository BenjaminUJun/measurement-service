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
  import time
  work_dir = ' /home/mininet/measurement-service/'
  if len(hosts) > 1:
    # fake one host as controller and send configuration messages to other hosts
    c = hosts[0]
    # set host2 as parent node of the rest nodes 
    l = []

  for i,h in enumerate(hosts):
    # test on other hosts
    if i > 0:
      ip = h.IP()  
      if i == len(hosts)-1:
        h.cmd('python' + work_dir + 'agent.py -a ' + ip + ' -l ' + '\''+str(l)+'\''+ ' &')
        h.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + ip + ' -f config_counters' + '&')
      else:
        h.cmd('python' + work_dir + 'agent.py -a ' + ip + ' &')
        l.append(h.IP())
      #h.cmd('python' + work_dir + 'monitor.py' + ' &') 
      #time.sleep(0.5)
      #c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + ip + ' -f config_sketch' + '&')

# send messages to do measurements
def send_msg(hosts):
  work_dir = ' /home/mininet/measurement-service/'
  if len(hosts) > 1:
    # fake one host as controller and send configuration messages to other hosts
    c = hosts[0]
    p = hosts[len(hosts)-1]
    ip = p.IP() 
    print c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + ip + ' -f query_counters' + '&')
#    print c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + ip + ' -f query_sketch' + '&')
#    print c.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + ip + ' -f query_heavy_hitters' + '&')

def clear_counters(hosts):
  work_dir = ' /home/mininet/measurement-service/'
  for i,h in enumerate(hosts):
    if i > 0: 
      ip = h.IP() 
      h.cmd('python' + work_dir + 'tests/config_counters.py' + ' -a ' + ip + ' -f clear_counters' + '&')

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
  CLI(net)
  net.pingAll()
  send_msg(net.hosts)
  CLI(net)
  clear_counters(net.hosts)
  net.stop()

if __name__ == '__main__':
  # Tell mininet to print useful information
  setLogLevel('info')
  simpleTest()
