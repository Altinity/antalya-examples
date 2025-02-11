#!/bin/bash
if [ "$1" != "-f" ]; then
    echo "This script deletes all live Docker containers and volumes!"
    echo "Run $0 -f to approve this level of destruction."
    exit 1
fi
echo "Killing live containers"
for c in $(podman ps -q)
do 
  podman kill $c; 
done
echo "Removing dead containers"
for c in $(podman ps -q -a)
do 
  podman rm $c; 
done
echo "Removing volumes"
for v in $(podman volume ls -q)
do 
  podman volume rm $v; 
done
