#!/bin/bash

for project in nova neutron keystone cinder swift ironic magnum glance
do
  python fetchbugs.py --username=mikalstill --project=glance
done
