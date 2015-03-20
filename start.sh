#!/bin/bash
X -nolisten tcp > /dev/null 2>&1 &
DISPLAY=:0.0 xset -dpms; DISPLAY=:0.0 xset s off
DISPLAY=:0.0 /usr/bin/python2 -u -m /home/pi/pishow/pishow/ /home/pi/pishow/Images $HOSTNAME > /home/pi/pishow/log.txt 2>&1 &
