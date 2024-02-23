#!/bin/bash

folder_path="./testing_suite"
extension="event"

find "$folder_path" -type f -name "*.$extension" | while read -r file; do
	echo "Running tests on $file"
	python3 sim.py LINK_STATE $file
done