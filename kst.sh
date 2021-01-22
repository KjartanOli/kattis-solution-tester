#! /bin/bash

declare -r RELEASE_NUM="1"
declare -r FEATURE_NUM="5"
declare -r HOTFIX_NUM="1"

declare -r VERSION="$RELEASE_NUM.$FEATURE_NUM.$HOTFIX_NUM"
declare -r AUTHOR="Kjartan Óli Ágústsson"


help()
{
	cat <<- _EOF_
	Usage kst [OPTIONS] PROBLEM SOLUTION
	Test a solution against the samples provided on Kattis
	OPTIONS:
	  -V, --version			Print version number
	  -i, --iceland			Problem on iceland.kattis
	  -h, --help			Print this help and exit
	  -o, --open			Problem on open.kattis
	  -s domain, --subdomain domain	Problem on subdomain.kattis.com
	  -v, --verbose			Print the output the solution being tested
	  -p2, --python2		Use Python2 instead of Python3
	_EOF_
}

parse_json()
{
	get_data | sed -e 's/\\u0026lt;/</g' | jq '.results[].text' | sed 's/^"//g' | sed 's/"$//g'
}

get_data()
{
	if [[ $subdomain == "iceland" ]]
	then
		cat <<- _EOF_
			{
				"results": $(curl -s "https://$subdomain.kattis.com/problems/iceland.$problem" | pup 'table.sample pre json{}')
			}
		_EOF_
	else
		cat <<- _EOF_
			{
				"results": $(curl -s "https://$subdomain.kattis.com/problems/$problem" | pup 'table.sample pre json{}')
			}
		_EOF_
	fi
}

version()
{
	cat <<- _EOF_
		kst (Kattis Solution Tester) $VERSION

		Written by $AUTHOR
	_EOF_
}

strip_whitespace()
{
	sed 's/ *$//'
}

determine_interpreter()
{
	if ((verbose))
	then
		echo "Determining filetype"
	fi
	case $solution in
		*.py)
			run="python$python"
			if ((verbose))
			then
				echo -e "File is python. Setting interpreter to python$python\n"
			fi
			;;
		*.js)
			run="node"
			if ((verbose))
			then
				echo -e "File is javascript. Setting interpreter to node\n"
			fi
			;;
		*.java)
			run="java"
			compiled=1
			compiler="javac"
			if ((verbose))
			then
				echo -e"File is Java. Setting compiler to javac\n"
			fi
			;;
		*.cpp)
			compiled=1
			compiler="g++"
			if ((verbose))
			then
				echo -e "File is C++. Setting compiler to g++\n"
			fi
			;;
		*.c)
			compiled=1
			compiler="gcc"
			if ((verbose))
			then
				echo -e "File is C. Setting compiler to gcc\n"
			fi
			;;
	esac
}


python=3
compiled=0
verbose=0
while [ $1 ]
do
	case $1 in
		-i | --iceland)
			subdomain="iceland"
			;;
		-o | --open)
			subdomain="open"
			;;
		-V | --version)
			version
			exit 0
			;;
		-h | --help)
			help
			exit 0
			;;
		-s | --subdomain)
			shift
			subdomain="$1"
			;;
		-v | --verbose)
			verbose=1
			;;
		-p2 | --python2)
			python=2
			;;
		*)
			if (($# == 2))
			then
				problem=$1
			elif (($# == 1))
			then
				solution=$1
			fi
			;;
	esac
	shift
done

c=0
# Replace space characters so that each sample is its own line
for i in $(parse_json | sed -e 's/ /\d26/g')
do
	# Replace '\n' characters in the json.
	i=$(echo -e $i)
	for x in $i
	do
		# Add space characters back in so the samples are correct
		x=$(echo $x | sed -e 's/\d26/ /g')
		echo $x
	done > "test$c"

	# Increment argc and assign to a garbage variable to avoid Command not found errors.
	t=$((c++))
done

i=0
while ((i < c))
do
	# Odd numbered files are output, even numbered files are input
	if ((i % 2 == 1))
	then
		mv "test$i" "out$((i / 2))"
	else
		mv "test$i" "in$((i / 2))"
	fi

	# Increment argc and assign to a garbage variable to avoid Command not found errors.
	t=$((i++))
done

samples=$(find -type f -name "in*" | wc -l)

determine_interpreter

if ((compiled))
then
	if [[ $compiler == "javac" ]]
	then
		java=1
	fi
	if ((verbose))
	then
		echo -e "Compiling\n"
	fi
	$compiler $solution
fi

i=0
while ((i < samples))
do
	if ((compiled))
	then
		if ((java))
		then
			if ((verbose))
			then
				echo -e "Testing solution against Sample Input $((i + 1))\nInput:"
				cat "in$i"
				echo "Output:"
				output=$($run $(echo $solution | sed 's/.java//g') | strip_whitespace)
				echo "$output"
				echo "Expected output:"
				cat "out$i"
				if [[ $output == $(cat "out$i") ]]
				then
					result="passed"
				else
					result="failed"
				fi
			else
				if [[ $($run $(echo $solution | sed 's/\.java//g') < "in$i" | strip_whitespace) == $(cat "out$i") ]]
				then
					result="passed"
				else
					result="failed"
				fi
			fi
		else
			if ((verbose))
			then
				echo -e "Testing solution against Sample Input $((i + 1))\nInput:"
				cat "in$i"
				echo "Output:"
				output=$(./a.out < "in$i" | strip_whitespace)
				echo "$output"
				echo "Expected output:"
				cat "out$i"
				if [[ $output == $(cat "out$i") ]]
				then
					result="passed"
				else
					result="failed"
				fi

			else
				if [[ $(./a.out < "in$i" | strip_whitespace) == $(cat "out$i") ]]
				then
					result="passed"
				else
					result="failed"
				fi
			fi
		fi
	else
		if ((verbose))
		then
			echo -e "Testing solution against Sample Input $((i + 1))\nInput:"
			cat "in$i"
			echo "Output:"
			output=$($run $solution < "in$i" | strip_whitespace)
			echo -e "$output\nExpected output:"
			cat "out$i"
			if [[ $output == $(cat "out$i") ]]
			then
				result="passed"
			else
				result="failed"
			fi
		else
			if [[ $($run $solution < "in$i" | strip_whitespace) == $(cat "out$i") ]]
			then
				result="passed"
			else
				result="failed"
			fi
		fi
	fi

	echo "Test $((i + 1)): $result"

	# Increment argc and assign to a garbage variable to avoid Command not found errors.
	t=$((i++))
	if ((verbose && i != (c / 2)))
		then
			echo
		fi
	done

# Clean up temporary files
find ./ -type f \( -name "in*" -o -name "out*" \) -delete
