#!/usr/bin/env python

import requests
import sys
import json
import re
from packaging import version


firmware_list = [
  [ 'MTX_1f177f7638f04b5c9b1d7830b1', 'BIOS DL380 Gen9/DL360 Gen9 (P89)'],
  [ 'MTX_054152dc642c4ea9bb690ea741', 'BIOS DL360 Gen10 (U32)' ],
  [ 'MTX_66b70385e3914913933aa5e389', 'BIOS DL380 Gen10' ],
  [ 'MTX_4a1ca73294cb40658faedadfb5', 'BIOS DL560 Gen10' ],
  [ 'MTX_71d71eb77aa14be48a032b73c9', 'ILO5' ],
  [ 'MTX_2a4f6e276e9d4eac9d3716e50b', 'ILO4' ],
  [ 'MTX_3f99fc1b32e54d7095b2172047', 'ILO3' ],
  [ 'MTX_0a99297a00de439093bc21e0df', 'Gen10 HBA SN1000Q' ],
  [ 'MTX_625d99e4cd3943d9b5c47ffb49', 'HPE Ethernet 10Gb 2-port 562T' ],
  [ 'MTX_6d4cf1530bf34b55a65111d132', 'SPS HPE Gen10' ],
  [ 'MTX_4bc70c2144b342688bb197912d', 'Gen10 NVMe Backplane PIC Firmware' ],
  [ 'MTX_447c285fa6b44c259f2e8d0ecf', 'Agentless Management Service (iLO 5) RHEL7' ],
]


def main():
  for i in firmware_list:
    swItemId = i[0]
    details  = i[1]

    print( "Checking: {0} : {1}".format(swItemId, details ))
    search( swItemId )



def build_url_api_detail(swItemId):
  return 'https://support.hpe.com/hpesc/public/api/software/{0}/detail'.format( swItemId )

def build_url_api_history(swItemId):
  return 'https://support.hpe.com/hpesc/public/api/software/{0}/history'.format( swItemId )

def build_url(swItemId):
  return 'https://support.hpe.com/hpsc/swd/public/detail?swItemId={0}#tab-history'.format( swItemId )


def validate_version( version ):
  # BIOS system version
  # 1.02_06-14-2017(18 Jul 2017)


  m = re.search('^(\d+\.\d+)_(\d{2}-\d{2}-\d{4})', version )
  if m:
    ver = m.group(1)
    ver_etc = m.group(2)
    return( ver, ver_etc)

  # ILO 2.30(4 Sep 2020)
  m = re.search('^([0-9\.]+)\((\d+\s\w+\s\d{4})\)$', version )
  if m:
    ver = m.group(1)
    ver_etc = m.group(2)
    return( ver, ver_etc)

  # 1.48(a) or 1.87 (C)
  m = re.search('^([0-9\.]+)\s?\(([a-z])\)$', version, re.IGNORECASE )
  if m:
    ver = m.group(1)
    ver_etc = m.group(2)
    return( ver, ver_etc)

  # ILO 2.19
  m = re.search('^([0-9\.]+)$', version )
  if m:
    ver = m.group(1)
    ver_etc = ""
    return( ver, ver_etc)

  #  2.75(b)(20 Aug 2020)
  m = re.search('^([0-9\.]+)\(([a-z])\)\((\d+\s\w+\s\d{4})\)$', version, re.IGNORECASE )
  if m:
    ver = m.group(1)
    ver_etc = "Version {0} : {1}".format( m.group(2), m.group(3))
    return( ver, ver_etc)

  #  1
  m = re.search('^(\d+)$', version )
  if m:
    ver = m.group(1)
    ver_etc = ""
    return( ver, ver_etc)

  print( 'No match for regex: ', version)
  sys.exit(1)



def search( req_swItemId ):
  version_data = []

  # Initial request to current detail
  url = build_url_api_detail( req_swItemId )
  r = requests.get( url )
  if r.status_code != 200:
    print("Failed Get for {}".format( url ))
    return

  firmware_detail = r.json()

  fm_id   = firmware_detail['swItemId']
  fm_desc = firmware_detail['swItem']['localizedTitle']
  fm_vers, fm_date = validate_version( firmware_detail['swItem']['versionId'] )


  # Now pull history to compare
  url = build_url_api_history( req_swItemId )

  r = requests.get( url )
  if r.status_code != 200:
    print("Failed Get for {}".format( url ))
    return

  firmware_history = r.json()

  for i in firmware_history['swHistory']:

    hist_id = i['itemId']
    hist_vers, hist_date = validate_version( i['versionId'] )
    version_data.append( [ hist_id, hist_vers, hist_date  ])

  # Now go through the available versions to find the newest
  high_ver = '0.0'
  for i in  version_data:
    their_ver = i[1]


    if version.parse( their_ver ) > version.parse( high_ver ):
      high_ver = their_ver
      high_swItemId = i[0]

  if version.parse(high_ver) > version.parse(fm_vers):
    print("    Please upgrade {0} to {1}".format( fm_vers, high_ver))
    print("    " +  build_url( high_swItemId ) + "\n" )


main()
