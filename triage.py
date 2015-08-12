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

    for priority in common.PRIORITIES:
        targets = bug_list.get(priority, [])
        random.shuffle(targets)
        for bug in targets:
            triages = common.triages(container, project, bug)
            if not common.recently_triaged(triages):
                print 'Bug %s (%s) is not triaged' %(bug, priority)
                print 'Triages: %s' % triages

                data = json.loads(container.get_object('%s-bug/%s'
                                                       %(project, bug)).get())
                for field in common.DISPLAY_ORDER:
                    print '%s: %s' %(field, data.get(field, ''))
                print 'tags: %s' % ' '.join(data.get('tags', []))
                print
                print 'Description:'
                print
                print data.get('description')
                print

                triage = {'reviewer': username}
                sys.stdout.write('OSIC (y/n)? ')
                triage['osic'] = sys.stdin.readline().rstrip()
                
                if triage['osic'] == 'y':
                    for question in common.QUESTIONS:
                        sys.stdout.write('%s? ' % question)
                        answer = sys.stdin.readline().rstrip()
                        triage[question] = answer

                common.clobber_object(container,
                                      '%s-bug/%s-%s' %(project, bug,
                                                       most_recent_datestamp),
                                      json.dumps(triage, indent=4,
                                                 sort_keys=True))
                print
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
