#!/usr/bin/python

# Take a list of bugs in an input file and turn it into something that can be
# imported into a spreadsheet

import argparse
import csv
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

    now = datetime.datetime.now()
    datestamp = '%04d%02d%02d' %(now.year, now.month, now.day)
    with open(list) as f:
        with open('%s.csv' % list, 'w') as csvfile:
            csvwriter = csv.writer(csvfile, dialect='excel')
            for bug in f.readlines():
                bug = bug.rstrip()

                try:
                    data = json.loads(container.get_object(
                        '%s-bug/%s' %(project, bug)).get())
                except pyrax.exceptions.NoSuchObject:
                    data = {}

                csvwriter.writerow([
                    'https://bugs.launchpad.net/nova/+bug/%s' % bug,
                    data.get('title', 'unknown'),
                    data.get('status', 'unknown'),
                    username])

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
