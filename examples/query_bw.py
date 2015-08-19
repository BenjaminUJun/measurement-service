def run(src,dst):
  import requests
  data = {}
  data['type'] = 'query bw'
  data['src'] = src
  data['dst'] = dst

  url = 'http://'+ src + ':8000'
  r = requests.post(url,data=data)
  print r.text

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='This is SoNIC server')
  parser.add_argument('-s','--src',help='src address',required=True)
  parser.add_argument('-d','--dst',help='dst address',required=True)
  args = parser.parse_args()
  run(args.src,args.dst)
