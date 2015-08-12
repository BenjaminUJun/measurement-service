import requests, subprocess

print '[test counter configuration...]'
url = "http://sonic3.cs.cornell.edu:8000"
data = {}
data['type'] = 'config counter'
data['interface'] = 'INPUT'
data['target'] = 'ACCEPT'
data['proto'] = 'icmp'
print "sending to" + url + " " + str(data)
response = requests.post(url, data = data)
print response.text

subprocess.call('timeout 3 ping google.com', shell=True)

print '[test counter querying...]'
url = "http://sonic3.cs.cornell.edu:8000"
data = {}
data['type'] = 'query counter'
data['proto'] = 'icmp'
print "sending to" + url + " " + str(data)
response = requests.post(url, data = data)
print response.text

print '[test sketch configuration...]'
url = "http://sonic3.cs.cornell.edu:8000"
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
