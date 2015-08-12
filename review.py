# See what triaged bugs have code reviews outstanding

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

    open_tabs = 0
    for priority in common.PRIORITIES:
        targets = bug_list.get(priority, [])
        for bug in targets:
            triages = common.triages(container, project, bug)
            if common.recently_triaged(triages):
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

                    print BUG_REPORT % bug_data

                    search = common.runcmd('ssh review.openstack.org gerrit '
                                           'query --current-patch-set '
                                           '--format=json \'message:" %s" '
                                           'status:open project:openstack/%s\''
                                           %(bug, project))
                    for line in search.split('\n'):
                        if len(line) < 1:
                            continue

                        d = json.loads(line.rstrip())
                        if d.get('id'):
                            print '    --> %s' % d['id']
                            approvals = d['currentPatchSet'].get('approvals', [])
                            for review in approvals:
                                print ('        %s: %s %s'
                                       %(review['by'].get('name'),
                                         review['type'],
                                         review['value']))
                            common.runcmd('chromium-browser '
                                          'https://review.openstack.org'
                                          '/#/q/%s,n,z' %(d['id']))
                            open_tabs += 1

            if open_tabs > 30:
                print
                print 'That\'s more than than thirty tabs!'
                print 'Press return for more...'
                sys.stdin.readline()
                open_tabs = 0

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
