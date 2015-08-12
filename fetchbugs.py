#!/usr/bin/python

# Fetch the current state of a project's bugs, and store that as a snapshot in
# cloudfiles.

import argparse
import datetime
import json
import os
import progressbar
import pyrax
import time

from launchpadlib import launchpad

import common


NOW = datetime.datetime.now()
LP_INSTANCE = 'production'
CACHE_DIR = os.path.expanduser('~/.launchpadlib/cache/')

PRIVATE_FIELDS = ['description', 'title']


def clobber_object(container, name, data):
    try:
        container.delete_object(name)
    except:
        pass
    container.store_object(name, data)

def main(username, project):
    pyrax.set_setting('identity_type', 'rackspace')
    with open(os.path.expanduser('~/.bugminion'), 'r') as f:
        conf = json.loads(f.read())
        pyrax.set_credentials(conf['access_key'],
                              conf['secret_key'],
                              region=conf['region'].upper())

    conn = pyrax.connect_to_cloudfiles(region=conf['region'].upper())
    container = conn.create_container(conf['container'])

    print 'Collecting bugs'
    today = {}
    lp = launchpad.Launchpad.login_with(username, LP_INSTANCE, CACHE_DIR)
    bugs = lp.projects[project].searchTasks(status=["New",
                                                    "Incomplete",
                                                    "Confirmed",
                                                    "Triaged",
                                                    "In Progress"])

    count = 0
    progress = progressbar.ProgressBar(maxval=bugs.total_size)
    progress.start()
    
    for bug in bugs:
        bug_data = {}

        for field in common.SAVED_FIELDS:
            bug_data[field] = bug.bug.__getattr__(field)
        for task in bug.bug.bug_tasks:
            if task.bug_target_name == project:
                today.setdefault(task.importance, [])
                today[task.importance].append(bug.bug.id)

                for field in common.SAVED_TASK_FIELDS:
                    bug_data[field] = task.__getattr__(field)

        # Sanitize fields for private security bugs
        if bug.bug.information_type == 'Private Security':
            for field in PRIVATE_FIELDS:
                bug_data[field] == '*** Embargoed Security Bug ***'

        # Sanitize date fields to something JSON can handle
        for field in bug_data:
            if field.startswith('date_') and bug_data[field]:
                bug_data[field] = time.mktime(bug_data[field].timetuple())

        # Write a project-centric view of this bug to cloudfiles
        object_name = '%s-bug/%s' %(project, bug_data['id'])
        common.clobber_object(container, object_name,
                              json.dumps(bug_data, indent=4, sort_keys=True))

        count += 1
        try:
            progress.update(count)
        except ValueError:
            # Believe it or not, if a bug is filed during the run, we crash
            # otherwise
            pass

    progress.finish()

    print 'Updating state map'
    common.clobber_object(container,
                          'nova/%04d%02d%02d' %(NOW.year, NOW.month, NOW.day),
                          json.dumps(today, indent=4, sort_keys=True))


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
