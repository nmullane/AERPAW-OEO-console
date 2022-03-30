#!/bin/bash

for i in {0..6}
do
    python3 portable_agent.py $i &
done
for i in {6..8}
do
    python3 fixed_agent.py $i &
done
for i in {8..10}
do
    python3 cloud_agent.py $i &
done
