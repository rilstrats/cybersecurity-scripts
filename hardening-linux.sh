#!/bin/bash

update_system() {
	if [[ -x $(command -v apt) ]]; then
		echo "Updating using apt, this may take a while..."
		sudo DEBIAN_FRONTEND=noninteractive apt-get update -yqq > /dev/null
		sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -yqq > /dev/null
		echo "Updating using apt is complete!"
	elif [[ -x $(command -v dnf) ]]; then
		echo "Updating using dnf, this may take a while..."
		sudo dnf upgrade -yq > /dev/null
		echo "Updating using dnf is complete!"
	else
		echo "Unsupported package manager, please upgrade manually"
	fi
}

sudoers=()

list_sudoers() {
	sudoers=( $(sudo cat /etc/sudoers |\
		sed '/^[[:space:]]*$/d' |\
		sed '/^#/d' |\
		sed '/^Defaults/d') )
}

# list_sudoers_groups() {
# 	list_sudoers | sed '/^[^%]/d'
# }
#
# list_sudoers_users() {
# 	list_sudoers | sed '/^[%]/d'
# }

check_sudoers() {
	list_sudoers
	echo here
	for sudoer in $sudoers; do
		echo $sudoer
		check_sudoer $sudoer
	done
}

yes_or_no=""

get_yes_or_no() {
	default="$1" # must be 'y' or 'n'
	prompt="${*:2}"
	while true; do
		read -p "$prompt"
		yes_or_no=$(echo -n ${REPLY:0:1} | tr '[:upper:]' '[:lower:]')
		if [[ $yes_or_no == "" ]]; then
			yes_or_no=$default
			break
		elif [[ $yes_or_no == "y" ]] || [[ $yes_or_no == "n" ]]; then
			break
		fi
	done
}

check_sudoer() {
	# echo -n "Should '$(echo -n $1 | cut -f 1)' user have '$(echo -n $1 | cut -f 2,3 | sed 's/\t/ /')' privileges? (Y/n): "
	# read
	# PRIVILEGED=$(echo -n ${REPLY:0:1} | tr '[:upper:]' '[:lower:]')
	# echo $PRIVILEGED
	sudoer="$1"
	privs="${@:2}"

	type=""
	if [[ "${sudoer:0:1}" == "%" ]]; then
		type="group"
	else
		type="user"
	fi

	get_yes_or_no "y" "Should '$sudoer' $type have "\
		"'$privs' privileges? (Y/n): "
	privileged=$yes_or_no
	echo $privileged

	get_yes_or_no "n" "Would you like this script to remove this user? " \
		"If not the changes must be made manually by you. (y/N): "
}

check_group() {
	# echo -n "Should '$(echo $1 | cut -f 1 | sed 's/%//')' group have '$(echo $1 | cut -f 2,3 | sed 's/\t/ /')' privileges? (Y/n): "
	# read
	# privileged=$(echo -n ${REPLY:0:1} | tr '[:upper:]' '[:lower:]')
	# echo $privileged
	get_yes_or_no "y" "Should '$(echo $1 | sed 's/%//')' group " \
		"have '$2 $3' privileges? (Y/n): "
	privileged=$yes_or_no
	if [[ $privileged = "y" ]]; then
		return
	fi

	get_yes_or_no "n" "Would you like this script to remove this group?" \
		"If not the changes must be made manually by you. (y/N): "

}

check_sudoers
