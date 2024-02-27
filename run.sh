#!/bin/bash
# runs all test cases in a given folder 

# Check if at least two arguments are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: sh $0 route_algorithm folder_path"
    exit 1
fi

extension="event"

find "$2" -type f -name "*.$extension" | while read -r file; do
	echo "Running tests on $file"
	python3 sim.py $1 $file
done