import requests
# request available bandwidth with JSON message
data = {'type' : 'query bw',\
'src' : '10.0.0.5',\
'dst' : '10.0.0.6'}

# tells src host to start bandwidth estimation
# agent listens on port 8000
url = 'http://10.0.0.5:8000'

r = requests.post(url,data=data)
# src host response with available bandwidth in MBytes/s
print r.text + ' MBytes/s'
