#!/usr/bin/python

# Review bugs in a way which scales across more than one person.

import argparse
import datetime
import json
import os
import progressbar
import pyrax
import time
import sys
import random

import common


def main(username, project, list):
    pyrax.set_setting('identity_type', 'rackspace')
    with open(os.path.expanduser('~/.bugminion'), 'r') as f:
        conf = json.loads(f.read())
        pyrax.set_credentials(conf['access_key'],
                              conf['secret_key'],
                              region=conf['region'].upper())

    conn = pyrax.connect_to_cloudfiles(region=conf['region'].upper())
    container = conn.create_container(conf['container'])

    # Prioritize a list of bugs from an input file
    now = datetime.datetime.now()
    datestamp = '%04d%02d%02d' %(now.year, now.month, now.day)
    with open(list) as f:
        for bug in f.readlines():
            bug = bug.rstrip()

            triage = {'reviewer': username,
                      'osic': 'y'}
            common.clobber_object(container,
                                  '%s-bug/%s-%s' %(project, bug, datestamp),
                                  json.dumps(triage, indent=4, sort_keys=True))

    print 'Done!'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch bugs from launchpad')
    parser.add_argument('--username')
    parser.add_argument('--project')
    parser.add_argument('--list')
    args = parser.parse_args()

    if not args.username:
        print 'Please specify a launchpad username'
        sys.exit(1)
    if not args.project:
        print 'Please specify a launchpad project'
        sys.exit(1)
    if not args.list:
        print 'Please specify a list of bug numbers (one per line)'
        sys.exit(1)
    
    main(args.username, args.project, args.list)
