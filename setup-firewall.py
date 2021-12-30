from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.addresses import IPAddr, EthAddr
from pox.firewall.sdnfirewall import * 
import csv
import sys
import re
import datetime

policy_filename = 'pox/firewall/config.pol'

def process_configuration(filename):
    '''
    This function imports the configure.pol file into the list "policies".  Each item in the list is a dictionary
    that includes all of the parsed data from the configuration file.  The dictionary keys for each item in the list
    are 'rulenum','action','mac-src','mac-dst','ip-src','ip-dst','ipprotocol','port-src','port-dst','comment' which
    corresponds to the directions in the configure.pol file.

    All imported data is a string.  Convert data as needed for the input into the POX match routines (or other possible
    implementations).

    This function also validates that the different addresses, ports, and protocol numbers are sensible and valid.  You
    do NOT need to further validate the input.
    '''

    fields = ('rulenum','action','mac-src','mac-dst','ip-src','ip-dst','ipprotocol','port-src','port-dst','comment')
    policies = []
    
    with open(filename,'r') as config_file:
        configuration = csv.DictReader(filter(lambda row: row[0]!='#', config_file),fieldnames=fields)
        try:
            for rule in configuration:
                
                # Validate Action Item
                if rule['action'] not in ('Block','Allow'):
                    raise ValueError('Invalid Action Item for rulenum %s: %s' % (rule['rulenum'],rule['action']))

                # Validate MAC Addresses
                if rule['mac-src'] != '-' and (None == re.match("[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$",rule['mac-src'].lower())):
                    raise TypeError("Invalid Format for Source MAC Address for rulenum %s" % rule['rulenum'])
                if rule['mac-dst'] != '-' and (None == re.match("[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$",rule['mac-dst'].lower())):
                    raise TypeError("Invalid Format for Destination MAC Address for rulenum %s" % rule['rulenum'])

                # Validate IP Addresses
                if rule['ip-src'] != '-' and (None == re.match("^(25[0-5]|2[0-4]\d|[01]\d{2}|\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]\d{2}|\d{1,2})){3}(/(3[012]|[12]\d|\d))$",rule['ip-src'])):
                    raise TypeError("Invalid Format for Source IP Address for rulenum %s" % rule['rulenum'])
                if rule['ip-dst'] != '-' and (None == re.match("^(25[0-5]|2[0-4]\d|[01]\d{2}|\d{1,2})(\.(25[0-5]|2[0-4]\d|[01]\d{2}|\d{1,2})){3}(/(3[012]|[12]\d|\d))$",rule['ip-dst'])):
                    raise TypeError("Invalid Format for Destination IP Address for rulenum %s" % rule['rulenum'])

                # Validate IP Protocol
                if (rule['ipprotocol'] != '-' and (int(rule['ipprotocol']) > 256 or int(rule['ipprotocol']) < -1)):
                    raise TypeError("Invalid IP Protocol for rulenum %s" % rule['rulenum'])

                # Validate Application Port
                if (rule['port-src'] != '-' and (int(rule['port-src']) > 65535 or int(rule['port-src']) < 0)):
                    raise TypeError("Invalid Source Application Port for rulenum %s" % rule['rulenum'])
                if (rule['port-dst'] != '-' and (int(rule['port-dst']) > 65535 or int(rule['port-dst']) < 0)):
                    raise TypeError("Invalid Destination Application Port for rulenum %s" % rule['rulenum'])

                if rule['ip-src'] != '-':
                    rule['ip-src-address'], rule['ip-src-subnet'] = rule['ip-src'].split("/")
                else:
                    rule['ip-src-address'], rule['ip-src-subnet'] = "-","-"
                if rule['ip-dst'] != '-':
                    rule['ip-dst-address'], rule['ip-dst-subnet'] = rule['ip-dst'].split("/")
                else:
                    rule['ip-dst-address'], rule['ip-dst-subnet'] = "-","-"

                policies.append(rule)

        except csv.Error:
            sys.exit()

    return policies

class SDNFirewall (EventMixin):
    
    def __init__ (self):
        self.listenTo(core.openflow)
        print("Starting POX Instance")
        print("Starting date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'\n\n')
        
    def _handle_ConnectionUp (self, event):
        
        policies = process_configuration(policy_filename)
        print("List of Policy Objects imported from configure.pol:")
        print("---------------------------------------------------")
        print(policies)
        rules = firewall_policy_processing(policies)
        for rule in rules:
            if rule is not None:
                event.connection.send(rule)
        
def launch ():
    core.registerNew(SDNFirewall)

def main():
    print("Starting POX Instance")
    print("Starting date and time : " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'\n\n')
    policies = process_configuration('configure.pol')
    print("List of Policy Objects imported from configure.pol:")
    print("---------------------------------------------------")
    print(policies)

if __name__ == "__main__":
    main()
