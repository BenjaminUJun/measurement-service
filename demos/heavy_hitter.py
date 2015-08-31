def config_sketch(addr):
  import requests
  data = {}
  data['type'] = 'config sketch'
  data['interface'] = 'INPUT'
  data['counter_key_type'] = 'src'
  data['dst'] = addr
  data['proto'] = 'udp'

  url = 'http://' + addr + ':8000'
  response = requests.post(url,data=data)

  return response.text

def config_sketch_counter(addr,sketch_id):
  import requests
  data = {}
  data['type'] = 'config sketch counter'
  data['sketch_id'] = sketch_id
  data['counter_key_type'] = 'src'

  url = 'http://' + addr + ':8000'
  response = requests.post(url,data=data)

  return response.text

def query_counter(addr, sketch_id, key, key_type):
  import requests
  data = {}
  data['type'] = 'query sketch'
  data['sketch_id'] = sketch_id
  data['counter_key_type'] = key_type
  data['counter_key'] = key
  
  url = 'http://' + addr + ':8000'
  response = requests.post(url,data=data)
  
  return response.text

def query_heavy_hitter(addr,sketch_id):
  import requests
  data = {}
  data['type'] = 'query heavy hitters'
  data['sketch_id'] = sketch_id
  data['counter_key_type'] = 'src'

  url = 'http://' + addr + ':8000'
  response = requests.post(url,data=data)

  return response

def run(addr,funct,sketch_id,key,key_type):
  if funct == 'config_sketch':
    i = config_sketch(addr)
    print 'sketch id: ' + str(i)
    config_sketch_counter(addr,i)
  if funct == 'query_heavy_hitter':
    if sketch_id >= 0:
      output = query_heavy_hitter(addr,sketch_id)
      if output.status_code == 200:
        import json,ast
        d = ast.literal_eval(output.text)
        print json.dumps(d,sort_keys=True,indent=4)
  if funct == 'query_counter':
    print query_counter(addr, sketch_id, key, key_type)

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Tests for network measurement')
  parser.add_argument('-a','--address',help='server address', required=True)
  parser.add_argument('-f','--function',help='options: config_sketch/query_counter/query_heavy_hitter', required=True)
  parser.add_argument('-i','--sketch_id',help='sketch id', default=-1)
  parser.add_argument('-k','--key',help='counter key', default='')
  parser.add_argument('-t','--key_type',help='counter key type', default='src')
  args = parser.parse_args()

  run(args.address,args.function,args.sketch_id,args.key,args.key_type)
