#!/bin/bash

for project in nova neutron keystone cinder swift ironic magnum glance ceilometer heat puppet rally horizon mistral magnum tempest keystone
do
  echo `date` "*** Fetching $project ***"
  python fetchbugs.py --username=mikalstill --project=$project

  echo `date` "*** Fetching python-"$project"client ***"
  python fetchbugs.py --username=mikalstill --project=python-$project"client"
done

echo `date` "*** Done ***"
