#!/bin/bash

# Check if wmctrl is installed
if command -v wmctrl &> /dev/null; then
    WM_NAME=$(wmctrl -m | grep "Name" | awk '{print $2}')
    if [ "$WM_NAME" == "KWin" ]; then
        python3 "./main.py"
    else
        python3 "./pyside.py"
    fi
elif command -v xprop &> /dev/null; then
    WM_NAME=$(xprop -root _NET_WM_NAME | cut -d ' ' -f 3-)
    if [ "$WM_NAME" == "KWin" ]; then
        python3 "./main.py"
    else
        python3 "./pyside.py"
    fi
else
    echo "Error somewhere. Sorry.."
fi

