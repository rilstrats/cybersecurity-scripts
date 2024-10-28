useradd badsudouser
sudo useradd badsudouser # add this user to /etc/sudoers
sudo useradd badsudousergroup
sudo useradd badsudogroup # add this group to /etc/sudoers
sudo usermod -aG sudo badsudousergroup
sudo cp /etc/sudoers /tmp/sudoers
echo  "\nbadsudouser\tALL=(ALL:ALL)\tALL\n%badsudogroup\tALL=(ALL:ALL)\tALL\n" | sudo tee -a /tmp/sudoers > /dev/null
sudo visudo -c -f /tmp/sudoers > /dev/null && \
	sudo cp /tmp/sudoers /etc/sudoers
sudo rm /tmp/sudoers
