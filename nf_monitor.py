import nfqueue
from scapy.all import *
import os
os.system('iptables -A OUTPUT -p icmp -j NFQUEUE')
def callback(payload):
    data = payload.get_data()
    pkt = IP(data)
    print pkt
    payload.set_verdict(nfqueue.ACCEPT)
def main():
    q = nfqueue.queue()
    q.open()
    q.bind(socket.AF_INET)
    q.set_callback(callback)
    q.create_queue(0)
    try:
        q.try_run() # Main loop
    except KeyboardInterrupt:
        q.unbind(socket.AF_INET)
        q.close()
        os.system('iptables -F')
        os.system('iptables -X')
main()
