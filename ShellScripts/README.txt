1. Edit autostart file:
nano ~/.config/lxsession/LXDE-pi/autostart


2.Add this to the end of the auto start file
@pathtofile/run_thonny.sh


3.Save and exit nano


4. Set shell scripts to execute!
chmod +x pathtofile/run_thonny.sh
