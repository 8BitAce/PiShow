#!/bin/bash
X -nolisten tcp > /dev/null 2>&1 &
DISPLAY=:0.0 xset -dpms; DISPLAY=:0.0 xset s off
DISPLAY=:0.0 /usr/bin/python2 -u /home/pishow/pishow/pishow/__main__.py /home/pishow/pishow/Images $HOSTNAME > /home/pishow/pishow/log.txt 2>&1 &
