useradd badsudouser
sudo useradd badsudouser # add this user to /etc/sudoers
sudo useradd badsudousergroup
sudo useradd badsudogroup # add this group to /etc/sudoers
sudo usermod -aG sudo badsudousergroup
