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
  if 'counter_key_type' in args:
    key_type = args['counter_key_type']
  else:
    key_type = 'src'
  if 'increment' in args:
    increment = args['increment']
  else:
    increment = 'pkt'
  sketch = SketchCounter(key_type,increment)
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
  def __init__(self,key_type='src',increment='pkt'):
    self.sketch = madoka.Sketch()
    self.total_counter = 0
    self.heavy_hitter = {}
    self.threshold = 0.1
    self.pkt_threshold = 5

    self.key_type = key_type
    self.increment = increment

  def count(self,pkt):
    pkt.accept()
    payload = IP(pkt.get_payload())		
    # extract counter key from packet
    if self.key_type == 'src_dst':
      # get the byte length of packet
      src = payload.getlayer(IP).src
      dst = payload.getlayer(IP).dst
      key = str(src) + ',' + str(dst)
    else:
      key = str(payload.getlayer(IP).src)
    # count increment    
    if self.increment == 'byte':
      byte_len = payload.getlayer(IP).len
      self.sketch[key] += byte_len
      self.total_counter += byte_len
    else:
      self.sketch[key] += 1
      self.total_counter += 1
    # do heavy hitter detection
    self.detect_heavy_hitter(key)

  def detect_heavy_hitter(self, key):
    if self.total_counter > self.pkt_threshold:
      if float(self.sketch[key])/float(self.total_counter) > self.threshold:
        self.heavy_hitter[key] = self.sketch[key]
      else:
        if key in self.heavy_hitter:
          del self.heavy_hitter[key]

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
    status_code = 200
    if 'type' in self.args:
      if self.args['type'] == 'config sketch':
        response = add_sketch(self.args)
      if self.args['type'] == 'query sketch':
        if ('sketch_id' in self.args) & ('counter_key' in self.args) :
          sketch_id = int(self.args['sketch_id'])
          key = self.args['counter_key']
          response = sketch_list[sketch_id].query_sketch(key)
        else:
          status_code = 400
          response = 'argument missing: sketch id or counter key'
      if self.args['type'] == 'query heavy hitters':
        if 'sketch_id' in self.args:
          sketch_id = int(self.args['sketch_id'])
          response = str(sketch_list[sketch_id].get_heavy_hitter()) 
        else:
          status_code = 400
          response = 'no sketch id specified'
     
    self.send_response(status_code)
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
