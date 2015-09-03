# add agent 
def add_leaf_agent(root_addr, leaf_addr):
  data = {}
  data['type'] = 'add leaf agent'
  data['agent_addr'] = leaf_addr
  
  url = 'http://' + root_addr + ':8000'
  r = requests.post(url,data=data)

# display leaf agents
def display_leaf_agents(root_addr):
  data = {}
  data['type'] = 'query leaf agents'
  
  url = 'http://' + root_addr + ':8000'
  r = requests.post(url,data=data)
  print r.text

def run(funct, root_addr, leaf_addr):
  if funct == 'add': 
    add_leaf_agent(root_addr,leaf_addr)
  if funct == 'display':
    display_leaf_agents(root_addr)

if __name__ == '__main__':
  import argparse, requests
  parser = argparse.ArgumentParser(description='Tests for network measurement')
  parser.add_argument('-r','--root_addr',help='root agent addr', required=True)
  parser.add_argument('-l','--leaf_addr',help='leaf agent addr', default = '')
  parser.add_argument('-f','--function',help='add/display', required=True)
  args = parser.parse_args()

  run(args.function,args.root_addr,args.leaf_addr)
