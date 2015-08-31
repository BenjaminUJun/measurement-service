def config_sketch(addr):
  import requests
  data = {}
  data['type'] = 'config sketch'
  data['interface'] = 'INPUT'

  url = 'http://' + addr + ':8000'
  response = requests.post(url,data=data)

  return response.text

def add_sketch_counter(addr,sketch_id,key_type):
  import requests
  data = {}
  data['type'] = 'config sketch counter'
  data['counter_key_type'] = key_type
  data['sketch_id'] = sketch_id

  url = 'http://' + addr + ':8000'
  response = requests.post(url,data=data)
  if __DEBUG: 
    print data
    print response.status_code
  return response.text

def query_heavy_hitter(addr,sketch_id,key_type):
  import requests
  data = {}
  data['type'] = 'query heavy hitters'
  data['sketch_id'] = sketch_id
  data['counter_key_type'] = key_type

  url = 'http://' + addr + ':8000'
  response = requests.post(url,data=data)

  return response

def get_real_time_counter(addr,sketch_id,key_type):
  import requests
  data = {}
  data['type'] = 'query real time counter'
  data['sketch_id'] = sketch_id
  data['counter_key_type'] = key_type

  print 'sending ' + str(data) + addr

  url = 'http://' + addr + ':8000'
  response = requests.post(url,data=data)

  return response

def detect_portscan(addr,sketch_id):
  import requests, time, re, collections
  update_cycle = 0.3
  key_num_threshold = 20
  key_num = 0
  new_key_num = 0
  while True:
    time.sleep(update_cycle)
    r = query_sketch(addr,sketch_id,'dport','real_time_key_num')
    if r.status_code == 200:
      key_num = new_key_num
      new_key_num = int(r.text)
    if new_key_num - key_num > key_num_threshold:
      print 'portscan detected.'
      r = get_real_time_counter(addr,sketch_id,'src_dport')
      if r.status_code == 200:
        ip_list = re.findall('\d+\.\d+\.\d+\.\d+',r.text)
        freq = collections.Counter(ip_list)
        print freq

def query_sketch(addr,sketch_id,key_type,key):
  import requests
  data = {}
  data['type'] = 'query sketch'
  data['sketch_id'] = sketch_id
  data['counter_key_type'] = key_type
  data['counter_key'] = key

  url = 'http://' + addr + ':8000'
  response = requests.post(url,data=data)

  return response

def run(addr,funct,sketch_id,key_type,key):
  if funct == 'config_sketch':
    i = config_sketch(addr)
    print 'sketch id: ' + str(i)
    add_sketch_counter(addr,i,'src_dport') 
    add_sketch_counter(addr,i,'dport') 
  if funct == 'query_heavy_hitter':
    if sketch_id >= 0:
      r = query_heavy_hitter(addr,sketch_id,key_type)
      if r.status_code == 200:
        import json,ast
        d = ast.literal_eval(r.text)
        print json.dumps(d,sort_keys=True,indent=4)
  if funct == 'query_sketch':
    if sketch_id >=0:
      r = query_sketch(addr,sketch_id,key_type,key)
      print r.text 
  if funct == 'detect_portscan':
    detect_portscan(addr,sketch_id)

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Tests for network measurement')
  parser.add_argument('-a','--address',help='server address', required=True)
  parser.add_argument('-f','--function',help='options: config_sketch/query_sketch/query_heavy_hitter/detect_portscan', required=True)
  parser.add_argument('-i','--sketch_id',help='sketch id', default=-1)
  parser.add_argument('-t','--key_type',help='type of counter key', default='dport')
  parser.add_argument('-k','--key',help='counter key', default='key_num')
  parser.add_argument('-d','--debug',help='debug option', default=False)
  args = parser.parse_args()

  __DEBUG = args.debug
  run(args.address,args.function,args.sketch_id,args.key_type,args.key)
