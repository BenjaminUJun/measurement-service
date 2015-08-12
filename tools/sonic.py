import sys, subprocess
def configure(post_msg):
  if(post_msg['type']=='est_req'):
    mode0 = 'pcs_app_cross'
    mode1 = 'pcs_app_cross'
    conf_cmd = ['/home/haoxian/sonic/driver/kernel/run_sonic.sh -m '+mode0+','+mode1]
    subprocess.check_output(conf_cmd, shell=True) 
