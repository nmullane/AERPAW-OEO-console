#!/bin/bash

for i in {0..11}
do
    python3 agent.py $i &
done
