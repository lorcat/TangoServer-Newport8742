#!/usr/bin/env bash

###
# Server variables
###
export SCRIPT_DIR="/home/tango/servers/Newport8742"
export TANGO_SERVER="Pico8742.py"
export TANGO_REF="LH"
export TANGO_DEBUG=""

# global variables
export TANGO_LOG="/tmp/tango"
mkdir -p $TANGO_LOG

#--
#   functions
#--


# make test of the device connectivity
# test of the device connectivity before running
function make_test {
        export TEST=`/usr/bin/lsusb | /bin/grep -i newport`
        if [ -z "$TEST" ]; then
                echo "Device is disconnected"
                exit -1
        else
                echo "Device is connected"
                echo "$TEST"
        fi

}

# locate server locally
function locate_server {
	echo "Moving the the script directory $SCRIPT_DIR"
	cd "$SCRIPT_DIR"

	if [ ! -z "$1" ]; then
	    export TANGO_REF="$1"
	fi

	if [ ! -z "$2" ]; then
	    export TANGO_DEBUG="$2"
	fi
}

# check exit code and restart the server in case of a trouble
function check_exit_code {
	if [ $EXIT_CODE == "0" ]; then
		# exited normally - we do nothing
        	echo "Exited normally - killed"
	else
		# some stupid error - crash - restart the server, notify the beamline scientist
	        echo "Strange error - let's restart the server"
        	$0 &
	fi

}


# ***
# Main code
# ***

# check the device for connection
make_test

# locate the server
locate_server

# starts the command
CMD="/usr/bin/python $TANGO_SERVER $TANGO_REF $TANGO_DEBUG'"
echo "Starting the command $CMD"
TANGO_LOG_PATH=$TANGO_LOG $CMD

# test exit code
echo "Tango server has quit with the code ($?)"
export EXIT_CODE="$?"
check_exit_code

exit 0
