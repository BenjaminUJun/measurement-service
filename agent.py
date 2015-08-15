#!/usr/bin/env python
 
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi, subprocess, requests, thread, argparse, time, re
import iptables

def send_probe():
  snd_cmd = ["/home/haoxian/pathload_1.3.2/pathload_snd"]
  subprocess.call(snd_cmd,shell=True); 
  
def inform_dst_host(src_addr,dst_addr):
  port_number = "8000"
  url = "http://"+dst_addr+":"+port_number
  data = {"type":"rcv_req","src_addr":src_addr,'dst_addr':dst_addr}
  data['update_addr'] = 'sonic3.cs.cornell.edu'
  data['update_port'] = 8080
  response = requests.post(url,data=data) 
  return response.text

def receive_probe(post_msg):
  from datetime import datetime
  rcv_cmd = ["/home/haoxian/pathload_1.3.2/pathload_rcv -s "+post_msg["src_addr"]]
  output=subprocess.check_output(rcv_cmd,shell=True) 
  [bw_min, bw_max] = parse_output(output)
  result={}
  result['type'] = "bw_update"
  result['time'] = datetime.now().time()
  result['src_addr'] = post_msg['src_addr']
  result['dst_addr'] = post_msg['dst_addr']
  result['minimum bandwidth']=bw_min 
  result['maximum bandwidth']=bw_max
      
  url = "http://"+post_msg['update_addr']+":"+post_msg['update_port']
  requests.post(url,data=result)

  return result

def parse_output(output):
  result_line = re.findall("range : [0-9]+\.[0-9]+ - [0-9]+\.[0-9]+", output); 
  result_str = result_line.pop() 
  [bw_min, bw_max] = re.findall("[0-9]+\.[0-9]+", result_str)
  return [bw_min, bw_max]

def do_bw_estimate(post_msg):
  src_addr = post_msg["src_addr"]
  dst_addr = post_msg["dst_addr"]
  if "cycle" in post_msg:
    cycle = post_msg["cycle"]
  else:
    cycle = 20   # default update circle is 20 seconds

  if "duration" in post_msg:
    duration = int(post_msg["duration"])
  else:
    duration = 60  # default update duration is 60 seconds

  if "method" in post_msg:
    method = post_msg["method"]
  else:
    method = "path_load"  # default method to estimate bandwidth is path_load
  
  if(method == "path_load"):
    for i in range(1,duration/cycle):
      thread.start_new_thread(send_probe,())
      time.sleep(1) 
      inform_dst_host(src_addr,dst_addr)

  if(method == "sonic"):
    sonic.configure(post_msg)
  
  return

def send_to_monitor(args):
  port = 9000
  url = 'http://127.0.0.1:' + str(port) 
  response = requests.post(url, data=args)
  return response.text

def recursive_query(args):
  [pkts_num,bytes_num] = iptables.read_counter(args)
  for a in leaf_agent:
    url = 'http://' + a + ':8000'
    output = requests.post(url, data=args)
    # parse output
    result = re.findall('[0-9]+',output.text)
    if len(result) > 1:
      [leaf_pkt, leaf_byte] = [int(result[0]),int(result[1])]
      pkts_num = pkts_num + leaf_pkt
      bytes_num = bytes_num + leaf_byte
  return [pkts_num,bytes_num]

def recursive_query_sketch(args):
  count = int(send_to_monitor(args))
  for addr in leaf_agent:
    url = 'http://' + addr + ':8000'
    output = requests.post(url,data=args)
    leaf_count = int(output.text)
    count = count + leaf_count
  return count
    
def recursive_query_heavy_hitter(args):
  from collections import Counter
  import ast 
  h_hitter = ast.literal_eval(send_to_monitor(args))
  for addr in leaf_agent:
    url = 'http://' + addr + ':8000' 
    output = requests.post(url,data=args)
    leaf_hitter = ast.literal_eval(output.text)
    h_hitter = Counter(h_hitter) + Counter(leaf_hitter)
  return dict(h_hitter)

class MyHandler(BaseHTTPRequestHandler):
  def do_POST(self):
    self.query_string = self.rfile.read(int(self.headers['Content-Length']))  
    self.args = dict(cgi.parse_qsl(self.query_string))
    response = "NULL"
    if 'type' in self.args:
      msg_type = self.args['type']
    else:
      self.send_response(200)
      self.end_headers()
      self.wfile.write("No message type indicated.")
      return

    if msg_type == 'est_req':
      thread.start_new_thread(do_bw_estimate,(self.args,))
      response = "Started Bandwidth Estimation"
    if msg_type == 'rcv_req':
      response = receive_probe(self.args)
    # handle traffic monitoring messages
    if msg_type == 'config counter':
      # send out configuration message to leaf agents
      for i,addr in enumerate(leaf_agent):
        url = 'http://'+str(addr)+':8000'
        requests.post(url,data=self.args)
      response = iptables.install_rules(self.args)  
    if msg_type == 'query counter':
      # recursive querying leaf agents
      response = recursive_query(self.args)
    if msg_type == 'config sketch':
      # send out configuration message to leaf agents
      for i,addr in enumerate(leaf_agent):
        url = 'http://' + str(addr) + ':8000'
        requests.post(url,data=self.args)
      response = send_to_monitor(self.args)
    if msg_type == 'query sketch':
      response = recursive_query_sketch(self.args)
    if msg_type == 'query heavy hitters':
      response = recursive_query_heavy_hitter(self.args)

    self.send_response(200)
    self.end_headers()
    self.wfile.write(str(response))
    return

  def do_GET(self):
    self.send_response(200)
    self.end_headers()
    self.wfile.write("This is SoNIC server")

def run(addr,port):
  print('http server is starting...')

  #ip and port of servr
  #by default http server port is 8000
  server_address = (addr,port)
  print server_address
  httpd = HTTPServer(server_address, MyHandler)
  print('server is listenning on host '+addr+':'+str(port))
  httpd.serve_forever()

# gloabal vriable: for storing the ip of leaf notes
leaf_agent = []

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='This is SoNIC server')
  parser.add_argument('-p','--port',help='server listen port',default=8000)
  parser.add_argument('-a','--address',help='server address', required=True)
  parser.add_argument('-l','--leaf',help='leaf host id',default=[])
  args = parser.parse_args()
  
  leaf_agent = leaf_agent + re.findall('[0-9]+.[0-9]+.[0-9]+.[0-9]+',str(args.leaf)) 
  
  run(args.address,int(args.port))
