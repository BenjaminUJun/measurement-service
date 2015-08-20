#!/usr/bin/env python
 
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi, subprocess, requests, thread, argparse, time, re
import iptables, iperf

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
  port = 9090
  url = 'http://127.0.0.1:' + str(port) 
  response = requests.post(url, data=args)
  return response

def recursive_query(args):
  [pkts_num,bytes_num] = iptables.read_counter(args)
  response = {}
  for a in leaf_agent:
    url = 'http://' + a + ':8000'
    r = requests.post(url, data=args)
    if r.status_code == 200:
      # parse output
      result = re.findall('[0-9]+',r.text)
      if len(result) > 1:
        [leaf_pkt, leaf_byte] = [int(result[0]),int(result[1])]
        pkts_num = pkts_num + leaf_pkt
        bytes_num = bytes_num + leaf_byte
    else:
      response['status_code'] = r.status_code
      response['data'] = r.text
  response['status_code'] = 200
  response['data'] = [pkts_num,bytes_num]
  return response

def recursive_query_sketch(args):
  r = send_to_monitor(args)
  print args
  response = {}
  if r.status_code == 200:
    print r.text
    count = int(r.text)
  else:
    response['status_code'] = r.status_code
    response['data'] = r.text
    return response

  for addr in leaf_agent:
    url = 'http://' + addr + ':8000'
    r = requests.post(url,data=args)
    if r.status_code == 200:
      leaf_count = int(r.text)
      count = count + leaf_count
    else:
      response['status_code'] = r.status_code
      response['data'] = r.text
      return response
      
  response['status_code'] = 200
  response['data'] = count
  return response
    
def recursive_query_heavy_hitter(args):
  from collections import Counter
  import ast 
  response = {'status_code':200,'data':{}}
  h_hitter = {}
  r = send_to_monitor(args)
  if r.status_code == 200:
    h_hitter = ast.literal_eval(r.text)
  else:
    response['status_code'] = r.status_code
    response['data'] = r.text
    return response

  for addr in leaf_agent:
    url = 'http://' + addr + ':8000' 
    r = requests.post(url,data=args)
    if r.status_code == 200:
      leaf_hitter = ast.literal_eval(r.text)
      h_hitter = Counter(h_hitter) + Counter(leaf_hitter)
    else:
      response['status_code'] = 500

  response['data'] = dict(h_hitter)
  return response

class MyHandler(BaseHTTPRequestHandler):
  def do_POST(self):
    self.query_string = self.rfile.read(int(self.headers['Content-Length']))  
    self.args = dict(cgi.parse_qsl(self.query_string))
    status_code = 400
    response = "error: message not parsed"
    if 'type' in self.args:
      msg_type = self.args['type']
    else:
      self.send_response(400)
      self.end_headers()
      self.wfile.write("No message type indicated.")
      return

    if msg_type == 'est_req':
      thread.start_new_thread(do_bw_estimate,(self.args,))
      response = "Started Bandwidth Estimation"
    if msg_type == 'rcv_req':
      response = receive_probe(self.args)

    if msg_type == 'query bw':
      r = iperf.query_bw(self.args)
      status_code = r['status_code']
      response = r['data']
    if msg_type == 'query jitter':
      r = iperf.query_jitter(self.args)
      status_code = r['status_code']
      response = r['data']
    if msg_type == 'config iperf server':
      if 'server_mode' in self.args:
        mode = self.args['server_mode']
        if iperf.start_server(mode) == 0:
          status_code = 200
          response = "iperf server started"
        else:
          status_code = 500
          response = "error: server failed"
      else:
        status_code = 400
        response = "bad requst: missing server mode"
    # handle traffic monitoring messages
    if msg_type == 'config counter':
      # send out configuration message to leaf agents
      for i,addr in enumerate(leaf_agent):
        url = 'http://'+str(addr)+':8000'
        requests.post(url,data=self.args)
      response = iptables.install_rules(self.args)  
    if msg_type == 'query counter':
      # recursive querying leaf agents
      r = recursive_query(self.args)
      status_code = r['status_code']
      response = r['data']
    if msg_type == 'config sketch':
      # send out configuration message to leaf agents
      for i,addr in enumerate(leaf_agent):
        url = 'http://' + str(addr) + ':8000'
        requests.post(url,data=self.args)
      r = send_to_monitor(self.args)
      status_code = r.status_code
      response = r.text
    if msg_type == 'config sketch counter':
      # send out configuration message to leaf agents
      for i,addr in enumerate(leaf_agent):
        # to config global counters on distributed end-hosts, may need to look up sketch id on each end-host, although in experiments they are the same
        url = 'http://' + str(addr) + ':8000'
        requests.post(url,data=self.args)
      r = send_to_monitor(self.args)
      status_code = r.status_code
      response = r.text
      
    if msg_type == 'query sketch':
      r= recursive_query_sketch(self.args)
      status_code = r['status_code']
      response = r['data']
    if msg_type == 'query heavy hitters':
      r = recursive_query_heavy_hitter(self.args)
      status_code = r['status_code']
      response = r['data']

    self.send_response(status_code)
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
