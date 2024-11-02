from input_gatherer import get_yes_or_no
from subprocess import DEVNULL, run
from os.path import isfile, isdir, expanduser
from os import mkdir
from datetime import datetime

class SSHConfigurer:

    sshd_config_file = []
    sshd_config_changed = False

    sshd_name = ""
    sshd_active = False
    sshd_enabled = False

    def run(self):
        self.backup_sshd_config()
        self.read_sshd_config()

        self.get_sshd_name()

        if self.sshd_name != "":
            self.check_sshd_server_status()
            self.audit_sshd_server()

        if self.sshd_active or self.sshd_enabled:
            self.audit_sshd_server_config()

        if self.sshd_config_changed:
            self.write_sshd_config()
            self.restart_sshd_server()

    def backup_sshd_config(self):
        now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        run(["sudo", "cp", "/etc/ssh/sshd_config",
             "/etc/ssh/sshd_config.{}.bkp".format(now)],
            capture_output=True, text=True)

        print("Backup created at /etc/ssh/sshd_config.{}.bkp".format(now))


    def read_sshd_config(self):
        with open("/etc/ssh/sshd_config") as infile:
            self.sshd_config_file = infile.readlines()

    def write_sshd_config(self):
        with open("/tmp/sshd_config", "w") as outfile:
            outfile.writelines(self.sshd_config_file)

        proc = run(["sudo", "cp", "/tmp/sshd_config", "/etc/ssh/sshd_config"])

        if proc.returncode == 0:
            print("Successfully configured SSH Server")

        else:
            print("Failure to configure SSH server")


    def restart_sshd_server(self):
        proc = run(["sudo", "systemctl", "restart", self.sshd_name],
                   stdout=DEVNULL)

        if proc.returncode == 0:
            print("Successfully restarted SSH Server")

        else:
            print("Failure to restart SSH server,",
                  "you might need to restore backup")

    def get_sshd_name(self):
        if isfile("/usr/lib/systemd/system/sshd.service"):
            self.sshd_name = "sshd"
        elif isfile("/usr/lib/systemd/system/ssh.service"):
            self.sshd_name = "ssh"


    def check_sshd_server_status(self):
        process = run(["systemctl", "is-active", "--quiet", self.sshd_name])

        if process.returncode == 0:
            self.sshd_active = True

        process = run(["systemctl", "is-enabled", "--quiet", self.sshd_name])

        if process.returncode == 0:
            self.sshd_enabled = True


    def audit_sshd_server(self):
        necessary = get_yes_or_no("Is SSH a necessary service?", True)

        if necessary and not self.sshd_enabled:
            print("SSH Server doesn't automatically run on startup.")
            prompt = "Would you like to make it run on startup?"
            enable = get_yes_or_no(prompt, True)
            if enable:
                proc = run(["sudo", "systemctl", "enable", self.sshd_name],
                           stdout=DEVNULL)
                if proc.returncode == 0:
                    print("Successfully enabled SSH Server")
                    self.sshd_enabled = True
                else: 
                    print("Failed to enable SSH server, please diagnose manually")

        if necessary and not self.sshd_active:
            print("SSH Server isn't running currently")
            prompt = "Would you like to start it?"
            enable = get_yes_or_no(prompt, True)
            if enable:
                proc = run(["sudo", "systemctl", "start", self.sshd_name],
                           stdout=DEVNULL)
                if proc.returncode == 0:
                    print("Successfully started SSH Server")
                    self.sshd_active = True
                else: 
                    print("Failed to start SSH server, please diagnose manually")

        if not necessary and (self.sshd_active or self.sshd_active):
            print("SSH Server is running or will run on startup")
            disable_now = get_yes_or_no("Would you like to turn it off?", True)

            if disable_now:
                proc = run(["sudo", "systemctl", "disable", "--now", self.sshd_name],
                           stdout=DEVNULL)
                if proc.returncode == 0:
                    print("Successfully stopped and disabled SSH Server")
                    self.sshd_active = False
                    self.sshd_enabled = False
                else: 
                    print("Failed to stop and disable SSH server,",
                          "please diagnose manually")

    def audit_sshd_server_config(self):
        self.configure_default_hardening()

        prompt = "Would you like to disable passwords and require SSH keys?"
        require_keys = get_yes_or_no(prompt, False)
        if require_keys:
            self.require_ssh_keys()

        disable_ipv6 = get_yes_or_no("Would you like to disable ipv6? ", True)
        if disable_ipv6:
            self.configure_line("AddressFamily", "inet")
    
    def require_ssh_keys(self):
        print("In order to set this option, you need an SSH key pair")
        confirmed = get_yes_or_no("Do you still want to move forward? ", False)
        if not confirmed:
            print("Please manually set up SSH keys later")
            return

        print("Use `ssh-keygen` to generate key pair")
        key = input("Copy and paste everything in the .pub file:\n").strip()
        if key == "":
            print("Please manually set up SSH keys later")
            return

        if not isdir(expanduser("~/.ssh")):
            mkdir(expanduser("~/.ssh"), 0o700)

        with open(expanduser("~/.ssh/authorized_keys"), "a") as appendfile:
            appendfile.write(key)

        print("Please SSH to the server and ensure that you can log in")
        ready = get_yes_or_no("Are you ready to require keys?", False)
        if not ready:
            print("Please manually set up SSH keys later")
            return

        options = [
            ("PubkeyAuthentication", "yes"),
            ("PasswordAuthentication", "no"),
            ("KbdInteractiveAuthentication", "no")
        ]
        
        for option in options:
            self.configure_line(option[0], option[1])

    def configure_default_hardening(self):
        options = [
            ("PermitRootLogin", "no"),
            ("MaxAuthTries", "3"),
            ("AllowAgentForwarding", "no"),
            ("AllowStreamLocalForwarding", "no"),
            ("AllowTcpForwarding", "no")
        ]

        for option in options:
            self.configure_line(option[0], option[1])


    def configure_line(self, keyword: str, argument: str):
        self.sshd_config_changed = True

        replaced = False
        for i in range(len(self.sshd_config_file)):
            if keyword + " " in self.sshd_config_file[i]:
                self.sshd_config_file[i] = keyword + " " + argument + "\n"
                replaced = True
                break

        if replaced == False:
            self.sshd_config_file.append(keyword + " " + argument + "\n")

