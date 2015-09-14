import subprocess, re, time

def run(switch, port):
  switch_name = ' "s' + switch + '" '
  cmd = 'ovs-ofctl dump-ports' + switch_name + str(port)
  output = subprocess.check_output(cmd, shell= True)
  result= re.findall('bytes=\d+', output)
  state1 = re.findall('\d+',str(result))
  print 'counting elapsed time...'
  t = time.time()
  subprocess.check_output('python tests/flow.py -f query -i 1', shell=True)
  elapsed_time = time.time() - t
  print 'timing finished'
  output = subprocess.check_output(cmd, shell=True)
  result= re.findall('bytes=\d+', output)
  state2 = re.findall('\d+',str(result))
  traffic = [int(state2[n])-int(state1[n]) for n in range(len(state1))]
  print 'traffic on' + switch_name + 'port ' +  port + ': ' + str(traffic)
  print 'elapsed_time: ' + str(elapsed_time)

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='This is SoNIC server')
  parser.add_argument('-s','--switch',help='',required=True)
  parser.add_argument('-p','--port',help='',required=True)
  args = parser.parse_args()
  run(args.switch, args.port)
