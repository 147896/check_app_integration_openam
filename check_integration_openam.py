#!/usr/bin/env python
# created by Gabriel Ribas (gabriel.ribass@gmail.com)
import requests, sys, json, getopt
import logging, httplib
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def quit(text, code):
   print('%s' %(text))
   sys.exit(code)

def metric(value, warn, crit):
   if not warn and not crit:
      return 0

   if warn <= crit:
      if value >= crit:
         return 2;
      elif value >= warn:
         return 1
      elif value < warn:
         return 0
      else:
         quit('Unable to check.', 3)
   elif warn > crit:
      if value <= crit:
         return 2
      elif value <= warn:
         return 1
      elif value > warn:
         return 0
      else:
         quit('Unable to check.', 3)

def usage():
   print(' Python Script - ::HELP::\n\
     -u | --username  # Informe o usuario\n\
     -p | --password  # Informe a senha\n\
     -r | --url       # Informe a url da aplicacao, node ou vip. Ex.: extranethml.unimedbh.com.br\n\
     -n | --port      # Informe a porta\n\
     -a | --context   # Informe o contexto da aplicacao. Ex.: consultorio\n\
     -s | --findstr   # Informe a string a ser pesquisada.\n\
     -w | --warning   # Informe o valor para warn\n\
     -c | --critical  # Informe o valor para critical\n\
     Syntax example.: \n\
                      ./check_integration_openam.py -u <username> -w <password> -r <app url> -p <port> -c <app context> -s <find string> -w <warn metric> -c <critical metric>\n\
                                         OR\n\
                      ./check_integration_openam.py --username=<username> --password=<password> --url=<app url> --port=<port> --context=<app context> --findstr=<find string> --warning=<warn metric> --critical=<critical metric>\n\
')

# getopt
opts, args = getopt.getopt(sys.argv[1:], 'hvu:p:r:n:a:s:w:c:', ['help', 
								'verbose', 
								'username=', 
								'password=', 
								'url=', 
								'port=', 
								'context=', 
								'findstr=', 
								'warning=', 
								'critical='])
try:
#if not opts:
#   usage()
#   sys.exit(2)

	if opts[0][0] == '-h' or opts[0][0] == '--help':
	   usage()
	   sys.exit(1)

	elif opts[0][1] and opts[1][1] and opts[2][1] and opts[3][1] and opts[4][1] and opts[5][1] and opts[6][1] and opts[7][1]:
	   username, password, url, port, context, findstr, warning, critical= opts[0][1], opts[1][1], opts[2][1], opts[3][1], opts[4][1], opts[5][1], opts[6][1], opts[7][1]

	elif opts[0][1] and opts[1][1] and opts[2][1] and opts[3][1] and opts[4][1] and opts[5][1] and opts[6][1] and opts[7][1]:
	   username, password, url, port, context, findstr, warning, critical = opts[0][1], opts[1][1], opts[2][1], opts[3][1], opts[4][1], opts[5][1], opts[6][1], opts[7][1]

	else:
	   usage()
	   sys.exit(2)

	for opt in opts:
	   if '-v' in opt:
	      httplib.HTTPConnection.debuglevel = 1
	      logging.basicConfig()
	      logging.getLogger().setLevel(logging.DEBUG)
	      requestsLog = logging.getLogger('requests.packages.urllib3')
	      requestsLog.setLevel(logging.DEBUG)
	      requestsLog.propagate = True
except IndexError:
   usage()
   sys.exit(2)
#        print('4-except')
#        usage()
#        sys.exit(2)

# URL Base OpenAM.
OpenAMBase = 'https://extranethml.unimedbh.com.br/openam/json'

headers = {
   'X-OpenAM-Username': '%s' %(username),
   'X-OpenAM-Password': '%s' %(password),
   'Content-Type': 'application/json'
}
data = "{\"uri\": \"ldapService\"}"

# OAM authenticate
try:
   response = requests.post('%s/authenticate' %(OpenAMBase), headers=headers, data=data, verify=False)
   auth_time = response.elapsed.total_seconds()
   tokenid = json.loads(response.text)['tokenId']
   cookie = response.cookies
   cookie.set('LtpaToken', '%s' %(cookie['LtpaToken']), domain='.unimedbh.com.br', path='/')
   cookie.set('LtpaToken2', '%s' %(cookie['LtpaToken2']), domain='.unimedbh.com.br', path='/')
   cookie.set('amlbcookiehx', '%s' %(cookie['amlbcookiehx']), domain='.unimedbh.com.br', path='/')
   cookie.set('TMP_COOKIE_AX_EXTRANET', '%s' %(cookie['TMP_COOKIE_AX_EXTRANET']), domain='extranethml.unimedbh.com.br', path='/')
   cookie.set('iPlanetDirectoryPro', '%s' %(tokenid), domain='.unimedbh.com.br', path='/')
except KeyError:
   print('Incapaz de recuperar o OpenAM Token\nUsuario ou senha invalida..')
   sys.exit(2)

# GET App 
try:
   response_app = requests.get('https://%s:%s/%s' %(url, port, context), cookies=cookie, verify=False)
   # App Time.
   app_time = response_app.elapsed.total_seconds()
except:
   print(response_app)
   sys.exit(2)

# OAM logout
response = requests.post('%s/sessions/?_action=logout' %(OpenAMBase), 
			  headers={'iPlanetDirectoryPro': '%s' %(tokenid), 
				   'Content-Type': '%s' %(headers['Content-Type'])}, 
			  	   verify=False)

# OpenAM logout time
logout_time = response.elapsed.total_seconds()

# sum time
total_time = auth_time + app_time + logout_time

# Find string
#if '%s' %(findstr) in response_app.text.encode('utf-8'):
if '%s' %(findstr) in response_app.text:
   msg = '%s / time: %ss | time=%ss;%s;%s;0;' %(findstr, total_time, total_time, warning, critical)
   exit = metric(total_time, warning, critical)
   quit(msg, exit)
else:
   print(response_app.text)
   sys.exit(2)
