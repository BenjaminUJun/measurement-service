import subprocess, re

def is_server_on():
  output = subprocess.check_output('ps',shell=True)
  result = re.findall('iperf',output) 
  return len(result) > 0

def start_server(mode='tcp'):
  if is_server_on():
    return 0
  else:
    if mode == 'udp':
      cmd = 'iperf -s -u &'
    else:
      cmd = 'iperf -s &'
    subprocess.call(cmd,shell=True)
    if is_server_on(): 
      return 0
    else:
      return -1

def start_remote_server(addr,mode = 'tcp'):
  import requests
  data = {}
  data['type'] = 'config iperf server'
  data['server_mode'] = mode
  url = 'http://' + addr + ':8000'
  
  response = requests.post(url, data=data)
  return response

def start_sender(addr):
  cmd = 'iperf -t 3 -f M -c' + str(addr)
  output = subprocess.check_output(cmd,shell=True)
  result_list = re.findall('[0-9]+ MBytes/sec+',output)
  bw = -1
  if len(result_list) > 0:
    s = result_list.pop()
    result = re.findall('[0-9]+',s)
    if len(result) > 0:
      bw = int(result.pop())
  return bw

def start_sender_udp(addr):
  cmd = 'iperf -t 3 -f M -u -c' + str(addr)
  output = subprocess.check_output(cmd,shell=True)
  result_list = re.findall('[0-9]+.[0-9]+ ms',output)
  jitter = -1
  if len(result_list) > 0:
    s = result_list.pop()
    result = re.findall('[0-9]+.[0-9]+',s)
    if len(result) > 0:
      jitter = float(result.pop())
  return jitter

def query_bw(args):
  response = {'status_code':400,'data':"error: bad request"}
  if 'dst' in args:
    dst = args['dst']
    r = start_remote_server(dst)
    if r.status_code == 200:
      bw = start_sender(dst)
      if bw > 0:
        # successfully done bandwidth estimation
        response['status_code'] = 200
        response['data'] = bw
      else:
        response['status_code'] = 500
        response['data'] = "error: internal error occured"
    else:
      response['status_code'] = r.status_code
      response['data'] = r.text
  else:
    response['status_code'] = 400
    response['data'] = "bad request: dst address missing"
      
  return response

def query_jitter(args):
  response = {'status_code':400,'data':"error: bad request"}
  if 'dst' in args:
    dst = args['dst']
    mode = 'udp'
    r = start_remote_server(dst,mode)
    if r.status_code == 200:
      jitter = start_sender_udp(dst)
      if jitter > 0:
        # successfully done bandwidth estimation
        response['status_code'] = 200
        response['data'] = jitter
      else:
        response['status_code'] = 500
        response['data'] = "error: internal error occured"
    else:
      response['status_code'] = r.status_code
      response['data'] = r.text
  else:
    response['status_code'] = 400
    response['data'] = "bad request: dst address missing"
      
  return response
