#!/usr/bin/python

import csv
import datetime
import json
import sys


report_start = datetime.datetime(2015, 7, 20) # Week 30, 2015

with open('metrics.json') as f:
    events = json.loads(f.read())

# Smoosh the events into weeks, not days
weekly_events = {}
for key in events:
    (year, month, day) = key.split('.')
    year = int(year)
    month = int(month)
    day = int(day)

    week = datetime.datetime(year, month, day).isocalendar()[1]
    wkey = '%s.%s' %(year, week)
    weekly_events.setdefault(wkey, {})

    for engineer in events.get(key, {}):
        weekly_events[wkey].setdefault(engineer, [])
        weekly_events[wkey][engineer].extend(events[key][engineer])

with open('metrics-weekly.json', 'w') as f:
    f.write(json.dumps(weekly_events, indent=4, sort_keys=True))

with open('metrics.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=['week starting', 'Code-Review',
                                                 'Workflow', 'commits',
                                                 'referenced-bugs',
                                                 'resolved-bugs'])
    writer.writeheader()

    d = report_start
    while d < datetime.datetime.now():
        summary = {'week starting': datetime.datetime.strftime(d, '%Y-%b-%d'),
                   'Code-Review': 0,
                   'Workflow': 0,
                   'commits': 0,
                   'referenced-bugs': 0,
                   'resolved-bugs': 0}
        try:
            week = d.isocalendar()[1]
            key = '%s.%s' %(d.year, week)
            for engineer in weekly_events.get(key, {}):
                for (event, value, project) in weekly_events[key][engineer]:
                    if event.startswith('Self-'):
                        event = event[len('Self-'):]
                    summary[event] += 1
        except Exception as e:
            print weekly_events[key][engineer]
            print
            print e
            sys.exit(1)

        writer.writerow(summary)

        d += datetime.timedelta(days=7)
