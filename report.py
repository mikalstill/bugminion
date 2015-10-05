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


NOW = datetime.datetime.now()


BUG_REPORT = """
%(id)s: %(title)s
    Link: %(web_link)s
    Priority: %(importance)s
    Status: %(status)s
    Date created: %(date_created_dt)s

"""


def main(username, project):
    pyrax.set_setting('identity_type', 'rackspace')
    with open(os.path.expanduser('~/.bugminion'), 'r') as f:
        conf = json.loads(f.read())
        pyrax.set_credentials(conf['access_key'],
                              conf['secret_key'],
                              region=conf['region'].upper())

    conn = pyrax.connect_to_cloudfiles(region=conf['region'].upper())
    container = conn.create_container(conf['container'])

    # Read the most recent bug dump
    most_recent = common.get_most_recent_dump(container, project)
    most_recent_datestamp = most_recent.split('/')[1]
    print 'Using the dump from %s' % most_recent

    bug_list = json.loads(container.get_objects(prefix=most_recent)[0].get())

    osic = []
    for priority in common.PRIORITIES:
        targets = bug_list.get(priority, [])
        triaged_count = 0
        for bug in targets:
            triages = common.triages(container, project, bug)
            if common.recently_triaged(triages):
                triaged_count += 1

                triage_data = json.loads(triages[-1].get())
                if triage_data['osic'] == 'y':
                    bug_files = container.get_objects(
                                    prefix='%s-bug/%s' %(project, bug))
                    for f in bug_files:
                        fname = f.name.split('/')[-1]
                        if fname.find('-') != -1:
                            continue
                        else:
                            bug_data = json.loads(f.get())

                    bug_data['date_created_dt'] = \
                        datetime.datetime.fromtimestamp(
                            bug_data['date_created'])

                    osic.append(BUG_REPORT % bug_data)

        if len(targets) > 0:
            print '%10s: %d of %d triaged' %(priority, triaged_count,
                                             len(targets))

    print '\n'.join(osic)
    print
    print 'Done!'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch bugs from launchpad')
    parser.add_argument('--username')
    parser.add_argument('--project')
    args = parser.parse_args()

    if not args.username:
        print 'Please specify a launchpad username'
        sys.exit(1)
    if not args.project:
        print 'Please specify a launchpad project'
        sys.exit(1)
    
    main(args.username, args.project)
