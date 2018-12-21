# How to do a re-install of the system

* Go to Settings>Dock and select "Auto-hide Dock"
* Go to Settings>Devices>Displays and set the resolution to 1024x768 (4:3)
* Go to the Ubuntu software app and search for "hide top bar" and install it. This will hide the top bar automatically when the animation is full screen
* Open a terminal instance with Ctrl+Alt+T
* Install git and pip with the following commands:
  * sudo apt-get update  sudo apt-get upgrade  sudo apt-get install git python3-pip -y
* Check to make sure they are installed by calling the following commands;
  * pip3 --version
  * git --version
* If there are version numbers, you're good
* Navigate to Documents and clone my github repo with the following command:
  * git clone https://github.com/dwells35/alien_eye.git
* Create a virtual environment in which to work
  * Run the following command using pip:
    * sudo pip3 install virtualenv virtualenvwrapper
  * Now we will update our ~/.bashrc file to include the following lines at the _bottom_ of the file
    * export WORKON_HOME=$HOME/.virtualenvs  
    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3  
    source /usr/local/bin/virtualenvwrapper.sh  
  * source the .bashrc file or close the terminal and start a new terminal instance
  * Go to Documents (or wherever you cloned the github repo) and cd into alien_eye
  * Next, let's create our virtual environment called "alien_eye" with the following command:
    * mkvirtualenv alien_eye -p python3 -r requirements.txt
  * Let's double check that our virtual environment is active by typing the followng command;
    * workon alien_eye
  * If everyting is successful, "(alien_eye)" should show up before our username in the terminal
  * Exit this virtual environment at any time by calling "deactivate" from the terminal
  * Now we need to install FlyCapture2 and PyCapture2


 
