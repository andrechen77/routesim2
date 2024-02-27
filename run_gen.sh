#!/bin/bash
# generates and runs a given number of random test cases

# Check if at least one arguments is provided
if [ "$#" -lt 2 ]; then
    echo "Usage: sh $0 route_algorithm num_cases"
    exit 1
fi

test_name="gen_cases/$1/gen_test"
output_name="gen_cases/$1/out"
failed=0

for ((i=1; i<=$2; i++)); do
    test_path="$test_name-$i"
	test_file="$test_path.event"
	output_file="$output_name-$i.txt"
	python3 generate_simulation.py --out $test_path
	echo "running test" $i
	python3 sim.py $1 $test_file>> $output_file
	# Check for errors raised during simulation
	if grep -q "incorrect" "$output_file"; then
		echo -e "Failed tests: $i"
		((failed++))
	else
		echo -e "Tests passed for event $i!"
		# clean up files
		rm $test_file
		rm $output_file
	fi
done

if [ "$failed" -eq 0 ]; then
    echo -e "\nALL $2 TESTS PASSED!! :)"
else
    echo -e "\n$failed out of $2 TESTS FAILED!! :("
fi