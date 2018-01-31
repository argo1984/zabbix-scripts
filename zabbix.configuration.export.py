#!/usr/bin/python

import sys
import argparse
import logging
import time
import os
import json
import xml.dom.minidom
from zabbix.api import ZabbixAPI
from sys import exit
from datetime import datetime
from pprint import pprint

#export = {
#        'templates': { 'method': 'template.get', 'id': 'templateid'},
#        'hostgroups': { 'method': 'hostgroup.get', 'id': 'groupid' },
#        'valueMaps': { 'method': 'valuemap.get', 'id': 'valuemapid' },
#        'hosts': { 'method': 'host.get', 'id': 'hostid' },
#        'screens': {'method': 'screen.get', 'id': 'screenids' },
#        'maps': {'method': 'map.get', 'id': 'sysmapids' },
#        'images': {'method': 'image.get', 'id': 'imageids'},
#        }
#
#
#pprint(export)
#
#for key in export:
#    print "Key: " + key
#    print export[key]['id']
#
#sys.exit(0)

parser = argparse.ArgumentParser(description='This is a simple tool to export zabbix templates for backup. Please note it will always set the data on export to 1/1/2016 so git wont update unless something substantial happens.')
parser.add_argument('--templates', help='Name of specific template to export',default='All')
parser.add_argument('--out-dir', help='Directory to output templates to.',default='../configuration')
parser.add_argument('--debug', help='Enable debug mode, this will show you all the json-rpc calls and responses', action="store_true")
parser.add_argument('--url', help='URL to the zabbix server (example: https://monitor.example.com/zabbix)',required = True)
parser.add_argument('--user', help='The zabbix api user',required = True)
parser.add_argument('--password', help='The zabbix api password',required = True)
args = parser.parse_args()

if args.debug:
  logging.basicConfig(level = logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
  logger = logging.getLogger(__name__)

def main():
  global args
  global parser

  if None == args.url :
    print "Error: Missing --url\n\n"
    exit(2)

  if None == args.user :
    print "Error: Missing --user\n\n"
    exit(3)

  if None == args.password :
    print "Error: Missing --password\n\n"
    exit(4)

  if False == os.path.isdir(args.out_dir):
    os.mkdir(args.out_dir)

  zm = ZabbixTemplates( args.url, args.user, args.password )

  zm.exportTemplates(args)

class ZabbixTemplates:

    def __init__(self,_url,_user,_password):
      self.zapi = ZabbixAPI(url=_url, user=_user, password=_password)

    def exportTemplates(self,args):
      export = {
        'templates': { 'method': 'template.get', 'id': 'templateid', 'name': 'host'},
        'groups': { 'method': 'hostgroup.get', 'id': 'groupid', 'name': 'name' },
        'valueMaps': { 'method': 'valuemap.get', 'id': 'valuemapid' },
        'hosts': { 'method': 'host.get', 'id': 'hostid' },
        'screens': {'method': 'screen.get', 'id': 'screenid' },
        'maps': {'method': 'map.get', 'id': 'sysmapid' },
        'images': {'method': 'image.get', 'id': 'imageid'},
        }

      request_args = {
      	"output": "extend"
      }

      if args.templates != 'All':
        request_args.filter = {
          "host": [args.tempaltes]
        }

      for key in export:
        print "LALALA"
        result = self.zapi.do_request(export[key]['method'],request_args)
        if not result['result']:
          print "No matching host found for '{}'".format(hostname)
          exit(-3)

        if result['result']:
          for t in result['result']:
            pprint(t)
            if False == os.path.isdir(args.out_dir+'/'+key):
              os.mkdir(args.out_dir+'/'+key)
            dest = args.out_dir+'/'+key+'/'+t['name']+'.xml'
            self.exportTemplate(t[export[key]['id']],dest,key)

    def exportTemplate(self,tid,oput,export):

      print "tempalteid:",tid," output:",oput
      args = {
        "options": {
            export: [tid]
        },
        "format": "xml"
      }

      result = self.zapi.do_request('configuration.export',args)
      template = xml.dom.minidom.parseString(result['result'].encode('utf-8'))
      date = template.getElementsByTagName("date")[0]
      # We are backing these up to git, steralize date so it doesn't appear to change 
      # each time we export the templates
      date.firstChild.replaceWholeText('2016-01-01T01:01:01Z')
      f = open(oput, 'w+')
      f.write(template.toprettyxml().encode('utf-8'))
      f.close()

class ZabbixHostgroups:

    def __init__(self,_url,_user,_password):
      self.zapi = ZabbixAPI(url=_url, user=_user, password=_password)

    def exportTemplates(self,args):
      request_args = {
        "output": "extend"
      }

      if args.templates != 'All':
        request_args.filter = {
          "host": [args.tempaltes]
        }

      result = self.zapi.do_request('hostgroup.get',request_args)
      if not result['result']:
        print "No matching host found for '{}'".format(hostname)
        exit(-3)

      if result['result']:
        for t in result['result']:
          #pprint(t)
          dest = args.out_dir+'/'+t['name']+'.xml'
          #print dest
          if False == os.path.isdir(args.out_dir+'/'+t['name']):
            os.mkdir(args.out_dir+'/'+t['name'])
          self.exportTemplate(t['groupid'],dest)

    def exportTemplate(self,tid,oput):

      print "tempalteid:",tid," output:",oput
      args = {
        "options": {
            "templates": [tid]
        },
        "format": "xml"
      }

      result = self.zapi.do_request('configuration.export',args)
      template = xml.dom.minidom.parseString(result['result'].encode('utf-8'))
      date = template.getElementsByTagName("date")[0]
      # We are backing these up to git, steralize date so it doesn't appear to change
      # each time we export the templates
      date.firstChild.replaceWholeText('2016-01-01T01:01:01Z')
      f = open(oput, 'w+')
      f.write(template.toprettyxml().encode('utf-8'))
      f.close()


if __name__ == '__main__':
  main()
