#!/usr/bin/python

import csv
import datetime
import json
import requests
import sys
import time

s = requests.session()


period_start = datetime.datetime(2015, 7, 1)
target_users = []

for company in ['Rackspace', 'Intel']:
    url = ('http://stackalytics.com/api/1.0/stats/engineers?company=%s'
           '&start_date=%d'
           %(company, time.mktime(period_start.timetuple())))
    print 'Fetching: %s' % url
    engineers = s.get(url).json()

    for engineer in engineers['stats']:
        if not engineer['id'] in target_users:
            target_users.append(engineer['id'])

print 'Found %d users' % len(target_users)

events = {}

for username in target_users:
    for metric in ['marks', 'commits', 'resolved-bugs']:
        d = datetime.datetime.now()
        count = 0
        while d > period_start:
            previous_d = d
            url = ('http://stackalytics.com/api/1.0/activity?'
                   'user_id=%s&page_size=100&start_record=%d&'
                   'metric=%s'
                    %(username, count * 100, metric))
            print 'Fetching: %s' % url

            reviews = s.get(url).json()
            count += 1

            for act in reviews['activity']:
                when = datetime.datetime.fromtimestamp(act['date'])
                d = when

                key = '%d.%d.%d' %(when.year, when.month, when.day)
                events.setdefault(key, {})
                events[key].setdefault(username, [])

                try:
                    bugs_referenced = act.get('bug_id_count', 0)
                    if bugs_referenced > 0:
                        events[key][username].append(('referenced-bugs',
                                                      bugs_referenced,
                                                      act['module']))

                    value_keys = {'marks': 'value',
                                  'commits': 'loc',
                                  'resolved-bugs': 'importance'}

                    events[key][username].append((act.get('type', metric),
                                                  act[value_keys[metric]],
                                                  act['module']))
                except Exception as e:
                    print
                    print url
                    print
                    print 'Could not process %s' % repr(act)
                    print
                    print e
                    sys.exit(1)


            if previous_d == d:
                break


with open('metrics.json', 'w') as f:
    f.write(json.dumps(events, indent=4, sort_keys=True))


print 'All ok'
