import sys
import madoka
from netfilterqueue import NetfilterQueue
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import thread, cgi
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *

# global sketch list
sketch_list= []

# method: add_sketch()
# description: 
#   initiate and add a count-min sketch to the global sketch list
#   then install a rule to iptables, which sends packets to nf queue
def add_sketch(args):
  import iptables
  global sketch_list
  # allocate an id to a new sketch
  sketch_id = len(sketch_list)
  sketch = SketchCounter()
  # add the new sketch to the global sketch list
  sketch_list.append(sketch)
  # install a rule to iptable, which sends targeted packets to nf queue
  construct_msg = {}
  construct_msg['interface'] = 'INPUT' 
  construct_msg['target'] = 'NFQUEUE'
  construct_msg['queue number'] = str(sketch_id)
  if 'proto' in args:
    construct_msg['proto'] = args['proto']
  if 'src' in args:
    construct_msg['src'] = args['src']
  if 'dst' in args:
    construct_msg['dst'] = args['dst']
  print iptables.install_rules(construct_msg)
  # bind the queue number with the sketch 
  nfqueue = NetfilterQueue()
  queue_num = sketch_id
  nfqueue.bind(queue_num, sketch_list[sketch_id].count)
  thread.start_new_thread(nfqueue.run,())
  return sketch_id

class SketchCounter():
  def __init__(self):
    self.sketch = madoka.Sketch()
    self.total_counter = 0
    self.heavy_hitter = {}
    self.threshold = 0.1
    self.pkt_threshold = 5

  def count(self,pkt):
    pkt.accept()
    print pkt
    payload = IP(pkt.get_payload())		
    src = str(payload.getlayer(IP).src)
    self.sketch[src] += 1
    self.total_counter += 1
    print 'total number:'+ str(self.total_counter)
    self.detect_heavy_hitter(src)

  def detect_heavy_hitter(self, src):
    if self.total_counter > self.pkt_threshold:
      if float(self.sketch[src])/float(self.total_counter) > self.threshold:
        self.heavy_hitter[src] = self.sketch[src]
        print "heavy hitter detected: %d hits" % self.sketch[src]
        print "src: "+ str(src) 
      else:
        if src in self.heavy_hitter:
          del self.heavy_hitter[src]

  def get_sum(self):
    return self.total_counter 

  def query_sketch(self,key):
    return self.sketch[key]
  
  def get_heavy_hitter(self):
    return self.heavy_hitter

class MyHandler(BaseHTTPRequestHandler): 
  def do_POST(self):
    self.query_string = self.rfile.read(int(self.headers['Content-Length']))  
    self.args = dict(cgi.parse_qsl(self.query_string))
    response = "NULL"
    if 'type' in self.args:
      if self.args['type'] == 'config sketch':
        response = add_sketch(self.args)
      if self.args['type'] == 'query sketch':
        if 'sketch id' in self.args:
          sketch_id = int(self.args['sketch id'])
        else:
          response = 'no sketch id specified'
        if 'counter key' in self.args:
          key = self.args['counter key']
        else:
          response = 'no counter key specified'
        response = sketch_list[sketch_id].query_sketch(key)
      if self.args['type'] == 'query heavy hitters':
        if 'sketch id' in self.args:
          sketch_id = int(self.args['sketch id'])
          response = str(sketch_list[sketch_id].get_heavy_hitter()) 
        else:
          response = 'no sketch id specified'
     
    self.send_response(200)
    self.end_headers()
    self.wfile.write(str(response))
    return

def run():
  port = 9000
  server_address = ("127.0.0.1",port)
  httpd = HTTPServer(server_address, MyHandler)
  print "monitor is listenning on port" + str(port)
  httpd.serve_forever() 

if __name__=='__main__':
  run()
