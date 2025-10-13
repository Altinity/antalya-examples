#!/bin/bash
if [ "$1" != "-f" ]; then
    echo "This script deletes all live Docker containers and volumes!"
    echo "Run $0 -f to approve this level of destruction."
    exit 1
fi
echo "Killing live containers"
for c in $(docker ps -q)
do 
  docker kill $c; 
done
echo "Removing dead containers"
for c in $(docker ps -q -a)
do 
  docker rm $c; 
done
echo "Removing volumes"
for v in $(docker volume ls -q)
do 
  docker volume rm $v; 
done
