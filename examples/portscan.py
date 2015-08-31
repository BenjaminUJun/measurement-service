import requests, json, time, ast, re, collections
# targeted end-host is h5
addr = "10.0.0.5"
# agent programs listen on port 8000
port = 8000

# --------------------------
# Configuration
# --------------------------

# a json message: to apply filter rules on targeted end-host
data = {'type':  'config sketch', \
'interface': 'INPUT'}
url = 'http://' + addr + ':' + str(port)
r = requests.post(url,data=data)

# Targeted end-hosts response with the sketch id
sketch_id = int(r.text)

# message to configure counter on the sketch
data = {'type': 'config sketch counter',\
'sketch_id': sketch_id,\
'counter_key_type': 'src_dport',\
'increment': 'pkt'}
r = requests.post(url,data=data)

# configure anothe counter to collect distribution data among dports
data = {'type': 'config sketch counter',\
'sketch_id': sketch_id,\
'counter_key_type': 'dport',\
'increment': 'pkt'}
r = requests.post(url,data=data)

# ---------------------------
# Query Counters periodically
# ---------------------------

key_num = 0
new_key_num = 0

while True:
  # for portscan detection, query interval should be shorter: 300ms
  time.sleep(0.3)

  # query how many disdinct keys are in the real time counter
  # to detect a burst in port access
  data={'type': 'query sketch', \
'sketch_id': sketch_id, \
'counter_key_type': 'dport',\
'counter_key': 'real_time_key_num'}
  # targetted end-host response with the number of disdinct keys in the real time counter
  r = requests.post(url,data=data)
  # use status code to guarantee a correct response. 200 for correct.
  if r.status_code == 200:
    key_num = new_key_num  
    new_key_num = int(r.text)
  # if the number of distinct requested port increased more than 20 in a single interval, a port scan is detected
  if new_key_num - key_num > 20:
    print 'portscan detected.'
    # query the real time traffic distribution among distinct <src addr, dst port> combination
    data={'type': 'query real time counter', \
'sketch_id': sketch_id, \
'counter_key_type': 'src_dport'}
    r = requests.post(url,data=data)
    if r.status_code == 200:
      ip_list = re.findall('\d+\.\d+\.\d+\.\d+',r.text)
      freq = collections.Counter(ip_list)
      print json.dumps(dict(freq),sort_keys=True,indent=4)
