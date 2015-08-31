import requests, json, time, ast
# targeted end-host is h5
addr = "10.0.0.5"
# agent programs listen on port 8000
port = 8000

# --------------------------
# Configuration
# --------------------------

# a json message: to apply filter rules on targeted end-host
data = {'type':  'config sketch', \
'interface': 'INPUT', \
'proto' : 'icmp'}
url = 'http://' + addr + ':' + str(port)
r = requests.post(url,data=data)

# Targeted end-hosts response with the sketch id
sketch_id = int(r.text)

# message to configure counter on the sketch
data = {'type': 'config sketch counter',\
'sketch_id': sketch_id,\
'counter_key_type': 'src',\
'increment': 'pkt'}
r = requests.post(url,data=data)

# ---------------------------
# Query Counters periodically
# ---------------------------

while True:
  # query counters every 5 seconds
  time.sleep(5)

  # query heavy hitter from the counter
  data={'type': 'query heavy hitters', \
'sketch_id': sketch_id, \
'counter_key_type': 'src'}
  # targetted end-host response with the heavy hitter records in JSON message
  r = requests.post(url,data=data)
  # parse text to json message
  d = ast.literal_eval(r.text)
  print json.dumps(d,sort_keys=True,indent=4)
  
  # query one counter entry by key
  data={'type': 'query sketch', \
'sketch_id': sketch_id, \
'counter_key_type': 'src',\
'counter_key': '10.0.0.6'}
  # targetted end-host response with the value
  r = requests.post(url,data=data)
  print 'h6 hits: ' +  r.text + 'times'
