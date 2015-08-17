def config_sketch(addr):
  import requests
  data = {}
  data['type'] = 'config sketch'
  data['interface'] = 'INPUT'
  data['counter_key_type'] = 'src_dst'

  url = 'http://' + addr + ':8000'
  response = requests.post(url,data=data)

  return response.text

def query_heavy_hitter(addr,sketch_id):
  import requests
  data = {}
  data['type'] = 'query heavy hitters'
  data['sketch_id'] = sketch_id

  url = 'http://' + addr + ':8000'
  response = requests.post(url,data=data)

  return response.text

def run(addr,funct,sketch_id):
  if funct == 'config_sketch':
    sketch_id = config_sketch(addr)
    print 'sketch id: ' + str(sketch_id)
  if funct == 'query_heavy_hitter':
    if sketch_id >= 0:
      print query_heavy_hitter(addr,sketch_id)

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Tests for network measurement')
  parser.add_argument('-a','--address',help='server address', required=True)
  parser.add_argument('-f','--function',help='options: config_sketch/query_sketch/query_heavy_hitter', required=True)
  parser.add_argument('-i','--sketch_id',help='sketch id', default=-1)
  args = parser.parse_args()

  run(args.address,args.function,args.sketch_id)
