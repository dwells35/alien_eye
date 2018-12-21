# How to do a re-install of the system
* Download Ubuntu ISO file from ubuntu.com
* Install Rufus
* Insert empty USB drive into computer (8gb or less USB drive is best because otherwise, it needs to be formatted to FAT32 first, though I think Rufus will automatically do that)
* Select “ISO Image” in “Create Bootable Disk Using” option
* Click the little disk icon beside the dropdown where you selected “ISO Image” and navigate to ISO file that you downloaded. Hit “Ok” or “Open” or whatever to select it. 
* It will tell you it’s a hybrid ISO, just proceed with the default option (ISO)
* Hit OK when it lets you know everything will be wiped
* Wait for ISO to be mounted to USB drive
* Once the ISO is mounted, make sure the NUC is powered off. 
* Plug the USB into the NUC, and power it on
* Hit “F2” like a madman until you get into the BIOS
* Change the boot order to look at the flashdrive with the ISO first
* Save and exit the BIOS
* You will now be asked what you want to do with Ubuntu – select ‘install Ubuntu’
* Go through the steps until it tells you that a version of Ubuntu is already on the computer
* Select “Re-install Ubuntu” to reinstall
* Finish steps and wait until installation is done
* Reboot
* Turn off automatic updates
  * Open "Software Updater" and select "Settings" after it is done checking for updates
  * Go to the dropdown for "Automatically check for updates" and select "Never"
* Go to Settings>Dock and select "Auto-hide Dock"
* Go to Settings>Devices>Displays and set the resolution to 1024x768 (4:3)
* Open the Ubuntu Software app and search for "hide top bar" and install it. This will hide the top bar automatically when the animation is full screen
* Open a terminal instance with Ctrl+Alt+T
* Install git and pip with the following commands:
  * sudo apt-get update  sudo apt-get upgrade  sudo apt-get install git python3-pip -y
* Check to make sure they are installed by calling the following commands;
  * pip3 --version
  * git --version
* If there are version numbers, you're good
* Navigate to Documents and clone my github repo with the following command:
  * git clone https://github.com/dwells35/alien_eye.git

# How to create a virtual environment in which to work
* Run the following command using pip:
* sudo pip3 install virtualenv virtualenvwrapper
* Now we will update our ~/.bashrc file to include the following lines at the _bottom_ of the file
* export WORKON_HOME=$HOME/.virtualenvs  
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3  
source /usr/local/bin/virtualenvwrapper.sh  
* source the .bashrc file (source ~/.bashrc from the command line) or close the terminal and start a new terminal instance
* Go to Documents (or wherever you cloned the github repo) and cd into alien_eye
* Next, let's create our virtual environment called "alien_eye" with the following command:
* mkvirtualenv alien_eye -p python3 -r requirements.txt
* Let's double check that our virtual environment is active by typing the followng command;
* workon alien_eye
* If everyting is successful, "(alien_eye)" should show up before our username in the terminal
* Exit this virtual environment at any time by calling "deactivate" from the terminal
* Now we need to install FlyCapture2 and PyCapture2

# How to install the correct version of PyCapture2

* Locate the PyCapture2 directory in the git repo or download a version of PyCapture from PTGrey's website (it will be followed by a version number; e.g. PyCapture2-2.13.31). The version provided in the git repo is for Ubuntu 18.04 and will not work with other verisons of Ubuntu.
* Ensure the the version of PyCapture you have downloaded matches the version of FlyCapture2 that you have.

* If FlyCapture2 is not yet installed, follow instructions provided by PTGrey for how to install it onto your system

* Using the bash terminal, navigate to your PyCatpture2 directory and see that you have the "setup.py" file

* Run the setup.py file USING THE VERSION OF PYTHON IN THE VIRTUAL ENVIRONMENT
  * From bash, run the following command (with your actual path):  
[your path]/python3 setup.py install
  * Your path will probably look like this if you setup your virtual environment in accordance with the other tutorial:  
~/.virtualenvs/[name of your virtual environment]/bin
  * Make sure that you have installed PyCapture into the virtual environment by navigating to the site-packages for the virtual environment and seeing that it is there (This will be in ~/.virtualenvs/[name of your virtual environment]/lib/python3.6/site-packages/
  * PyCapture2 will most likely show up as version 0.0.0, and I'm not sure why. As long as you use the correct setup.py file, it will work.
 
