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
      for i,val in enumerate(leaf_agent):
        url = '10.0.0.'+str(val)+':8000'
        requests.post(url,data=self.args)
      response = iptables.install_rules(self.args)  
    if msg_type == 'query counter':
      [pkts_num,bytes_num] = iptables.read_counter(self.args)
      response = [pkts_num,bytes_num]
      for i,val in enumerate(leaf_agent):
        url = '10.0.0.'+str(val)+':8000'
        [leaf_pkt,leaf_byte] = requests.post(url,data=self.args) 

    # unfinished here

    if msg_type == 'config sketch':
      response = send_to_monitor(self.args)
    if msg_type == 'query sketch':
      response = send_to_monitor(self.args)
    if msg_type == 'query heavy hitters':
      response = send_to_monitor(self.args)

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
  
  leaf_agent = leaf_agent + re.findall('[0-9]+',str(args.leaf)) 
  
  run(args.address,int(args.port))
