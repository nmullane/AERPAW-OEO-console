#!/bin/bash

for i in {0..8}
do
    python3 node.py $i &
done
