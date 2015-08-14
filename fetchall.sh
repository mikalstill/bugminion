#!/bin/bash

for project in nova neutron keystone cinder swift ironic magnum glance
do
  echo "*** Fetching $project ***"
  python fetchbugs.py --username=mikalstill --project=$project

  echo "*** Fetching python-"$project"client ***"
  python fetchbugs.py --username=mikalstill --project=python-$project"client"
done
