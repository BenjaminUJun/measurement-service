import requests, subprocess, argparse

parser = argparse.ArgumentParser(description='Tests for network measurement')
parser.add_argument('-a','--address',help='server address', required=True)
args = parser.parse_args()

url = 'http://' + args.address + ':8000'

print '\n[test counter configuration...]'
data = {}
data['type'] = 'config counter'
data['interface'] = 'INPUT'
data['target'] = 'ACCEPT'
data['proto'] = 'icmp'
print "sending to " + url + " " + str(data)
response = requests.post(url, data = data)
print response.text

print "pinging h2 for 3 times"
subprocess.call('timeout 3 ping 10.0.0.2', shell=True)

print '\n[test counter querying...]'
data = {}
data['type'] = 'query counter'
data['proto'] = 'icmp'
print "sending to " + url + " " + str(data)
response = requests.post(url, data = data)
print response.text

print "cleaning iptable rules"
subprocess.call('iptables -F INPUT', shell=True)

print '\n[test sketch configuration...]'
data = {}
data['type'] = 'config sketch'
data['interface'] = 'INPUT'
data['proto'] = 'icmp'
print "sending to " + url + " " + str(data)
response = requests.post(url, data = data)
print response.text

print "pinging h2 for 7 times..."
subprocess.call('timeout 7 ping 10.0.0.2', shell=True)

print '[test sketch query...]'
data = {}
data['type'] = 'query sketch'
data['sketch id'] = '0'
data['counter key'] = '10.0.0.2'
print "sending to" + url + " " + str(data)
response = requests.post(url, data = data)
print response.text

print '[test heavy hitter query...]'
data = {}
data['type'] = 'query heavy hitters'
data['sketch id'] = '0'
print "sending to" + url + " " + str(data)
response = requests.post(url, data = data)
print response.text

print "cleaning iptable rules"
subprocess.call('iptables -F INPUT', shell=True)
