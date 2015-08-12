import sys
import madoka
from netfilterqueue import NetfilterQueue
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import thread, cgi
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *

threshold = 0.1
sketch = madoka.Sketch()
total_counter = 0
heavy_hitter = {}

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

class MyHandler(BaseHTTPRequestHandler): 
  def do_POST(self):
    self.query_string = self.rfile.read(int(self.headers['Content-Length']))  
    self.args = dict(cgi.parse_qsl(self.query_string))
    response = "NULL"
    if 'type' in self.args:
      if self.args['type'] == 'query sketch':
        if 'counter key' in self.args:
          key = self.args['counter key']
          response = sketch[key]
      else:
        if self.args['type'] == 'query heavy hitters':
          response = str(heavy_hitter)

    self.send_response(200)
    self.end_headers()
    self.wfile.write(str(response))
    return
 

def run():
  nfqueue = NetfilterQueue()
  queue_num = 1

  port = 9000
  server_address = ("127.0.0.1",port)
  httpd = HTTPServer(server_address, MyHandler)
  print "monitor is listenning on port" + str(port)
  thread.start_new_thread(httpd.serve_forever,()) 

  counter1 = SketchCounter()
  nfqueue.bind(queue_num, counter1.count)
  try:
      nfqueue.run()
      print 'after nfqueue runs'
  except KeyboardInterrupt:
      print

if __name__=='__main__':
  run()
