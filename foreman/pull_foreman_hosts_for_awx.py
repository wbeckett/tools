#!/usr/bin/env python3

import foreman_config as cfg
import requests
import math
import sys
import tempfile, os, json

from jinja2 import Environment


if not cfg.CERTIFICATE_AS_STRING:
  print("cfg.CERTIFICATE_AS_STRING not set");
  sys.exit(1)

if not cfg.foreman_server:
  print("cfg.foreman_server not set");
  sys.exit(1)

if not cfg.api_key:
  print("cfg.api_key not set");
  sys.exit(1)

if not cfg.user:
  print("cfg.user not set");
  sys.exit(1)

groups = { 
  'host_group': {},
  'puppet_env': {},
  'content_name': {},
  'lifecycle': {},
  'all': {},
   }



def get_page( cert, per_page=200, page=1, results=[] ):
  url = "https://{0}/api/hosts?per_page={1}&page={2}".format( cfg.foreman_server,per_page, page )
  #r = requests.get( url, auth=(cfg.user, cfg.api_key), cert=cert.name)
  r = requests.get( url, auth=(cfg.user, cfg.api_key), verify=cert.name)

  data = r.json()

  results.extend( data['results'] )

  total_entries = data['total']
  total_pages   = math.ceil(total_entries/per_page)
  #print( data['total'], total_pages, page)

  if total_pages > page:
    page = page + 1
    get_page( page=page, results=results )


  return results


def main():
  cert = tempfile.NamedTemporaryFile(delete=False)
  cert.write(cfg.CERTIFICATE_AS_STRING.encode(encoding='UTF-8') )
  cert.close()

  for server in get_page( cert ):

    if 'environment_name' in server:
      host_environment = server['environment_name']
    else:
      host_environment = None

    host_name       = server['name']
    host_group_name = server['hostgroup_title']
    host_id         = server['id']
    host_ipaddress  = server['ip']
    host_mac        = server['mac']

    if 'content_facet_attributes' in server:
      host_content_name   = server['content_facet_attributes']['content_view_name']
      host_lifecycle_name = server['content_facet_attributes']['lifecycle_environment_name']
    else:
      host_content_name   = None
      host_lifecycle_name = None
      

    # Populate host group
    if host_group_name not in groups['host_group']:
      groups['host_group'][ host_group_name ] = [ host_name ]
    else:
      groups['host_group'][ host_group_name ].append( host_name)

    # Populate ( puppet ) enviorment - puppet_env
    if host_environment not in groups['puppet_env']:
      groups['puppet_env'][ host_environment ] = [ host_name ]
    else:
      groups['puppet_env'][ host_environment ].append( host_name)

    # Populate the content enviroment - content_name
    if host_content_name not in groups['content_name']:
      groups['content_name'][ host_content_name ] = [ host_name ]
    else:
      groups['content_name'][ host_content_name ].append( host_name)  

    # Populate the content enviroment - lifecycle
    if host_lifecycle_name not in groups['lifecycle']:
      groups['lifecycle'][ host_lifecycle_name ] = [ host_name ]
    else:
      groups['lifecycle'][ host_lifecycle_name ].append( host_name)  


    # Populate the "all" group
    if host_name not in groups['all']:
      groups['all'][ host_name ] = { 'host_id': host_id, 'ansible_host': host_ipaddress, 'host_mac': host_mac }
    

  # Build expected data structure
  output_data = {}
  output_data['_meta'] = {}
  output_data['_meta']['hostvars'] = {}

  # All hosts group
  temp = []
  for h in groups['all']:
    temp.append( h )
    output_data['_meta']['hostvars'][ h] = groups['all'][ h ]

  output_data['all'] = temp


  print(json.dumps(output_data, indent=4))
  os.unlink(cert.name)


main()
