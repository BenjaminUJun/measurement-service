def config_sketch(addr):
  import requests
  data = {}
  data['type'] = 'config sketch'
  data['interface'] = 'OUTPUT'

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

  return response.text

def run(addr,funct,sketch_id,key_type):
  if funct == 'config_sketch':
    i = config_sketch(addr)
    print 'sketch id: ' + str(i)
    print add_sketch_counter(addr,i,'dport') 
    print 'added counter to sketch ' + str(i) + ' key type:' + 'dport'
    add_sketch_counter(addr,i,'dst') 
  if funct == 'query_heavy_hitter':
    if sketch_id >= 0:
      print query_heavy_hitter(addr,sketch_id,key_type)

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Tests for network measurement')
  parser.add_argument('-a','--address',help='server address', required=True)
  parser.add_argument('-f','--function',help='options: config_sketch/query_sketch/query_heavy_hitter', required=True)
  parser.add_argument('-i','--sketch_id',help='sketch id', default=-1)
  parser.add_argument('-t','--key_type',help='type of counter key', required=True)
  args = parser.parse_args()

  run(args.address,args.function,args.sketch_id,args.key_type)
