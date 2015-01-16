# README #

PiShow is a simple Python application to display content using a Raspberry Pi.

### What is PiShow? ###

PiShow listens to a specified Dropbox folder and displays images uploaded there on the connected monitor.

### Requirements ###
Python 2.x  
Dropbox python module  
feh  

### How do I get set up? ###

1. Create a Dropbox account and add a folder that will contain uploaded images.
2. In the pishow/ directory create a file named `app_key.txt` with the first line being the app key, the second being the app_secret.
3. Create a local directory on the Pi for the images (probably in pishow/).
4. Create a text file named `config.txt` and upload it to that Dropbox folder in step 2. (See Configuration below).
5. Run the program like so: `python pishow.py <local_directory> <remote_directory>` (e.x.: `python pishow.py Images Photos/PiImages`)
6. For the first run the program will walk you through authenticating with Dropbox. Subsequent runs will already be authenticated.
7. Done!  

**NOTE**: You will most likely want to run the program in some sort of run script to have it shutdown gracefully. A sample bash script is included as exec.sh.sample. Simply copy the file to exec.sh and edit the appropriate directories in the file.

### Configuration ###
Configuration is done using the file 'config.txt' that resides with the images in your Dropbox folder. Each line of the configuration file can specify a variable followed by a space and then the value. The variables are as follows (value types are in <>):  
`delay<integer>` The amount of time that elapses before transitioning images.  
`update_interval<integer>` The amount of time that elapses before pishow checks for new files/config.