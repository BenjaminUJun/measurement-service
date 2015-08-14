import requests

def config_counters(url):
  print '\n[test counter configuration...]'
  data = {}
  data['type'] = 'config counter'
  data['interface'] = 'INPUT'
  data['target'] = 'ACCEPT'
  data['proto'] = 'icmp'
  print "sending to " + url + ": " + str(data)
  response = requests.post(url, data = data)
  print response.text

def query_counters(url):
  print '\n[test counter querying...]'
  data = {}
  data['type'] = 'query counter'
  data['proto'] = 'icmp'
  print "sending to " + url + " " + str(data)
  response = requests.post(url, data = data)
  print response.text

def config_sketch(url):
  print '\n[test sketch configuration...]'
  data = {}
  data['type'] = 'config sketch'
  data['interface'] = 'INPUT'
  data['proto'] = 'icmp'
  print "sending to " + url + " " + str(data)
  response = requests.post(url, data = data)
  print response.text

def query_sketch(url):
  print '\n[test sketch query...]'
  data = {}
  data['type'] = 'query sketch'
  data['sketch id'] = '0'
  data['counter key'] = '10.0.0.2'
  print "sending to" + url + " " + str(data)
  response = requests.post(url, data = data)
  print response.text

def query_heavy_hitters(url):
  print '\n[test heavy hitter query...]'
  data = {}
  data['type'] = 'query heavy hitters'
  data['sketch id'] = '0'
  print "sending to" + url + " " + str(data)
  response = requests.post(url, data = data)
  print response.text

def clear_counters(url):
  import subprocess
  subprocess.call('iptables -F INPUT',shell=True)
  subprocess.call('iptables -F FORWARD',shell=True)
  subprocess.call('iptables -F OUTPUT',shell=True)

def run_test(addr, funct): 
  url = 'http://' + addr + ':8000'
  if funct == 'config_counters':
    config_counters(url)
  if funct == 'query_counters':
    query_counters(url)
  if funct == 'config_sketch':
    config_sketch(url)
  if funct == 'query_sketch':
    query_sketch(url)
  if funct == 'query_heavy_hitters':
    query_heavy_hitters(url)
  if funct == 'clear_counters':
    clear_counters()

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Tests for network measurement')
  parser.add_argument('-a','--address',help='server address', required=True)
  parser.add_argument('-f','--function',help='options: config_counters/query_counters/config_sketch/query_sketch/query_heavy_hitters/clear_counters', required=True)
  args = parser.parse_args()

  run_test(args.address,args.function)
