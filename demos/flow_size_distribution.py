def config_sketch(addr):
  import requests
  data = {}
  data['type'] = 'config sketch'
  data['interface'] = 'INPUT'
  data['proto'] = 'udp'

  url = 'http://' + addr + ':8000'
  response = requests.post(url,data=data)
  
  if __DEBUG:
    import json
    print json.dumps(data,indent=4)

  return response.text

def config_sketch_counter(addr,sketch_id):
  import requests
  data = {}
  data['type'] = 'config sketch counter'
  data['sketch_id'] = sketch_id
  data['counter_key_type'] = 'src_dst'
  data['increment'] = 'byte'

  url = 'http://' + addr + ':8000'
  response = requests.post(url,data=data)
  
  if __DEBUG:
    import json
    print json.dumps(data,indent=4)

  return response.text

def query_heavy_hitter(addr,sketch_id):
  import requests
  data = {}
  data['type'] = 'query heavy hitters'
  data['sketch_id'] = sketch_id
  data['counter_key_type'] = 'src_dst'

  url = 'http://' + addr + ':8000'
  response = requests.post(url,data=data)

  return response

def run(addr,funct,sketch_id):
  if funct == 'config_sketch':
    sketch_id = config_sketch(addr)
    print 'sketch id: ' + str(sketch_id)
    config_sketch_counter(addr,sketch_id)
  if funct == 'query_heavy_hitter':
    if sketch_id >= 0:
      r = query_heavy_hitter(addr,sketch_id)
      if r.status_code == 200:
        import json,ast
        d = ast.literal_eval(r.text)
        print json.dumps(d,sort_keys=True,indent=4)

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Tests for network measurement')
  parser.add_argument('-a','--address',help='server address', required=True)
  parser.add_argument('-f','--function',help='options: config_sketch/query_sketch/query_heavy_hitter', required=True)
  parser.add_argument('-i','--sketch_id',help='sketch id', default=-1) 
  parser.add_argument('-d','--debug',help='debug option', default=False)
  args = parser.parse_args() 

  __DEBUG = args.debug
  run(args.address,args.function,args.sketch_id)
