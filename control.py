#!/usr/bin/env python
 
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import requests, cgi, argparse

class MyHandler(BaseHTTPRequestHandler):
  def do_POST(self):
    self.query_string = self.rfile.read(int(self.headers['Content-Length']))  
    self.args = dict(cgi.parse_qsl(self.query_string))
    response = "NULL"
    print self.args
    if "type" in self.args:
      msg_type = self.args["type"]
    else:
      self.send_response(200)
      self.end_headers()
      self.wfile.write("No message type indicated.")
      return

    if msg_type == 'config sketch':
      addr = self.args['address']
      url = 'http://' + addr  + ':8000' 
      output = requests.post(url,data=self.args)
      response = output.text

    if msg_type == 'bw_update':
      print self.args
      response = "Update acknowledged."
      return

      self.send_response(200)
      self.end_headers()
      self.wfile.write(response)

  def do_GET(self):
# check if server is running
    self.send_response(200)
    self.end_headers()
    self.wfile.write("Hello, this is controller for Network Measurement.")


def run(sid,port):
  server_address = ("sonic"+str(sid)+".cs.cornell.edu",port)
  httpd = HTTPServer(server_address, MyHandler)
  print('controller is listenning on sonic'+str(sid)+' port:'+str(port))
  httpd.serve_forever()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='This is controller')
  parser.add_argument('-p','--port',help='controller listen port',default=8080)
  parser.add_argument('-i','--sid',help='sonic server id', required=True)
  args = parser.parse_args()

  run(int(args.sid),int(args.port))
