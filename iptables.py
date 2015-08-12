def install_rules(args):
  import subprocess
  cmd = 'iptables -I '
  if 'interface' in args:
    interface = args['interface']
  else:
    interface = 'INPUT'
  cmd = cmd + interface
  if 'proto' in args:
    cmd = cmd + ' -p ' + args['proto']
  if 'src' in args:
    cmd = cmd + ' -s ' + args['src']
  if 'dst' in args:
    cmd = cmd + ' -d ' + args['dst']
  if 'target' in args:
    cmd = cmd + ' -j ' + args['target'] 
  if 'queue number' in args:
    cmd = cmd + ' --queue-num ' + args['queue number']
  try:
    subprocess.check_output(cmd, shell=True)
    check_cmd = 'iptables -L ' + interface
    output = subprocess.check_output(check_cmd, shell=True)
    return output
  except subprocess.CalledProcessError as e:
    return e.output
  
def read_counter(args):
  import subprocess, re
  cmd = 'iptables -L ' 
  pattern = '.+[0-9].+'
  pkt_num = -1
  byte_num = -1
  if 'interface' in args:
    cmd = cmd + args['interface']
  else:
    cmd = cmd + 'INPUT'
  cmd = cmd + ' -v '
  if 'proto' in args:
    pattern = pattern + args['proto'] 
  if 'src' in args:
    pattern = pattern + args['src']
  if 'dst' in args:
    pattern = pattern + args['dst']
  try:
    output =  subprocess.check_output(cmd, shell=True)
    result_list = re.findall(pattern, output)
    if len(result_list) > 0:
      result_line = result_list.pop() 
      result = re.findall('[0-9]+', result_line)
      if len(result) > 1:
         [pkt_num, byte_num] = [result[0],result[1]]
  except subprocess.CalledProcessError as e:
    return e.output
  return [pkt_num, byte_num]
