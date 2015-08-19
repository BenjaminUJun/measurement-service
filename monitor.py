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
  s = Sketch()
  # add the new sketch to the global sketch list
  sketch_list.append(s)
  # install a rule to iptable, which sends targeted packets to nf queue
  construct_msg = {}
  construct_msg['interface'] = args['interface']
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
  nfqueue.bind(queue_num, sketch_list[sketch_id].iterate_counters)
  thread.start_new_thread(nfqueue.run,())
  return sketch_id

def add_sketch_counter(args):
  global sketch_list
  response = {'status_code':200,'data':''}
  if 'counter_key_type' in args:
    key_type = args['counter_key_type']
  else:
    response['status_code'] = 400
    response['data'] = "bad request: request missing type of counter key"
    return response

  if 'increment' in args:
    increment = args['increment']
  else:
    increment = 'pkt'
  if 'hitter_threshold' in args:
    hitter_threshold = args['hitter_threshold']
  else:
    hitter_threshold = 0.1

  if 'sketch_id' in args:
    sketch_id = int(args['sketch_id'])
    c = SketchCounter(key_type,increment,hitter_threshold)
    sketch_list[sketch_id].add_counter(c)
    response['data'] = "counter added: " + key_type,increment + str(hitter_threshold)
  else:
    response['status_code'] = 400
    response['data'] = "bad request: request missing sketch id"

  print len(sketch_list[sketch_id].counter_list)
  return response  

class Sketch():
  def __init__(self):
    self.counter_list = []
  
  def add_counter(self,c):
    self.counter_list.append(c)
  
  def iterate_counters(self,pkt):
    pkt.accept()
    for c in self.counter_list:
      c.count(pkt)
 
  def query_counter(self,key_type,key):
    response={'status_code':400,'data':"error: key not found"}
    for c in self.counter_list:
      if c.key_type == key_type:
        response['data'] = c.query_sketch(key)
        response['status_code'] = 200
    return response
  
  def get_heavy_hitter(self,key_type):
    response={'status_code':400,'data':"error: key not found"}
    for c in self.counter_list:
      if c.key_type == key_type:
        response['data'] = c.get_heavy_hitter()
        response['status_code'] = 200
    return response

class SketchCounter():
  def __init__(self,key_type='src',increment='pkt',hitter_threshold=0.1):
    self.sketch = madoka.Sketch()
    self.total_counter = 0
    self.heavy_hitter = {}
    self.threshold = hitter_threshold
    self.pkt_threshold = 5

    self.key_type = key_type
    self.increment = increment

  def count(self,pkt):
    payload = IP(pkt.get_payload())		
    src = payload.getlayer(IP).src
    dst = payload.getlayer(IP).dst
    if (src == '127.0.0.1') | (dst=='127.0.0.1'):
      # skip the local traffic
      return
    # extract counter key from packet
    if self.key_type == 'src_dst':
      # get the byte length of packet
      key = str(src) + ',' + str(dst)
    elif self.key_type == 'dst':
      key = str(dst)
    elif self.key_type == 'dport':
      if hasattr(payload.getlayer(IP),'dport'):
        key = str(payload.getlayer(IP).dport)
      else:
        return
    else:
      # collect src addr distribution by default
      key = str(src)
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
    response = "error: message not parsed"
    status_code = 400 
    if 'type' in self.args:
      if self.args['type'] == 'config sketch':
        statuu_code = 200
        response = add_sketch(self.args)
      if self.args['type'] == 'config sketch counter':
        status_code = 200
        response = add_sketch_counter(self.args)
      if self.args['type'] == 'query sketch':
        if ('sketch_id' in self.args) & ('counter_key_type' in self.args) & ('counter_key' in self.args) :
          sketch_id = int(self.args['sketch_id'])
          key_type = self.args['counter_key_type']
          key = self.args['counter_key']
          if sketch_id < len(sketch_list):
            r = sketch_list[sketch_id].query_counter(key_type,key)
            status_code = r['status_code']
            response = r['data']
        else:
          status_code = 400
          response = 'argument missing: sketch id or counter key'
      if self.args['type'] == 'query heavy hitters':
        if ('sketch_id' in self.args) & ('counter_key_type' in self.args):
          sketch_id = int(self.args['sketch_id'])
          key_type = self.args['counter_key_type']
          if sketch_id < len(sketch_list):
            r = sketch_list[sketch_id].get_heavy_hitter(key_type)
            status_code = r['status_code']
            response = r['data']
        else:
          status_code = 400
          response = 'sketch id or type of counter key is missing'
     
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
