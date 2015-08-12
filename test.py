import requests, subprocess

print '[test counter configuration...]'
url = "http://10.0.0.1:8000"
data = {}
data['type'] = 'config counter'
data['interface'] = 'INPUT'
data['target'] = 'ACCEPT'
data['proto'] = 'icmp'
print "sending to" + url + " " + str(data)
response = requests.post(url, data = data)
print response.text

subprocess.call('timeout 3 ping 10.0.0.2', shell=True)

print '[test counter querying...]'
url = "http://10.0.0.1:8000"
data = {}
data['type'] = 'query counter'
data['proto'] = 'icmp'
print "sending to" + url + " " + str(data)
response = requests.post(url, data = data)
print response.text

print '[test sketch configuration...]'
url = "http://10.0.0.1:8000"
data = {}
data['type'] = 'config sketch'
data['interface'] = 'INPUT'
data['target'] = 'ACCEPT'
data['proto'] = 'icmp'
print "sending to" + url + " " + str(data)
#response = requests.post(url, data = data)
#print response.text

print "cleaning iptable rules"
subprocess.call('iptables -F INPUT', shell=True)
