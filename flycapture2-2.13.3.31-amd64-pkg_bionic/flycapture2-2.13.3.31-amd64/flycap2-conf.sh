#!/bin/bash

set -o errexit

MY_PROMPT='$ '
MY_YESNO_PROMPT='(y/n)$ '

grpname="flirimaging"

if [ "$(id -u)" = "0" ]
then
    echo
    echo "This script will assist users in configuring their udev rules to allow";
    echo "access to 1394 and USB devices. The script will create a udev rule which";
    echo "will add the 1394 cards and USB devices to a group called flirimaging.";
    echo "The user may also choose to restart the udev daemon. All of this can be done";
    echo "manually as well.  Please note that this script will change the permissions";
    echo "for all IEEE1394 devices including hard drives and web cams. It will allow";
    echo "the user to read and modify data on any IEEE1394 device.";
    echo
    echo
else
    echo
    echo "This script needs to be run as root.";
    echo "eg.";
    echo "sudo flycap2-conf";
    echo
    exit 0
fi

while :
do
    echo "Enter the name of the user to add to this user group.";

    echo -n "$MY_PROMPT"
    read usrname
    echo "Is this user name ok?: $usrname";
    echo -n "$MY_YESNO_PROMPT"
    read confirm

    if [ $confirm = "y" ] || [ $confirm = "Y" ] || [ $confirm = "yes" ] || [ $confirm = "Yes" ]
    then
        break
    fi
    done

echo
echo "Add user $usrname to group $grpname.";
echo "Is this ok?:";
echo -n "$MY_YESNO_PROMPT"
read confirm

if [ $confirm = "y" ] || [ $confirm = "Y" ] || [ $confirm = "yes" ] || [ $confirm = "Yes" ]
then
    groupadd -f $grpname
    usermod -a -G $grpname $usrname
else
    echo
    echo "$usrname was not added to group $grpname.  Please configure your devices manually";
    echo "or re-run this script.";
    exit 0
fi

UdevFile="/etc/udev/rules.d/40-flir.rules";
echo
echo "Writing the udev rules file.";
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"2000\", MODE=\"0664\", GROUP=\"$grpname\"" 1>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"2001\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"2002\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"2003\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"2004\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"2005\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3000\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3001\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3004\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3005\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3006\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3007\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3008\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"300A\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"300B\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3100\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3101\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3102\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3103\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3104\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3105\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3106\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3107\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3108\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3109\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "ATTRS{idVendor}==\"1e10\", ATTRS{idProduct}==\"3300\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "KERNEL==\"raw1394\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "KERNEL==\"video1394*\", MODE=\"0664\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "SUBSYSTEM==\"firewire\", GROUP=\"$grpname\"" 1>>$UdevFile
echo "SUBSYSTEM==\"usb\", GROUP=\"$grpname\"" 1>>$UdevFile


echo
echo "Do you want to restart the udev daemon?";
echo -n "$MY_YESNO_PROMPT"
read confirm

if [ $confirm = "y" ] || [ $confirm = "Y" ] || [ $confirm = "yes" ] || [ $confirm = "Yes" ]
then
    /etc/init.d/udev restart
else
    echo
    echo "Udev was not restarted.  Please reboot the computer for the rules to take effect.";
    exit 0
fi

echo
echo "Configuration complete. A reboot may be required on some systems for changes to take effect";
echo

exit 0
