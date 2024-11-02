from enum import Enum
from subprocess import DEVNULL, run
from input_gatherer import get_yes_or_no
from getpass import getuser
from datetime import datetime
from os import remove

class SudoerType(Enum):
    UNDEFINED = -1
    USER = 0
    GROUP = 1

    def __str__(self):
        if self == SudoerType.USER:
            return "user"
        else:
            return "group"

class Sudoer:
    name = ""
    type = SudoerType.UNDEFINED
    privs = ""

    def __str__(self) -> str:
        return_string = ""
        if self.type == SudoerType.GROUP:
            return_string += "%"

        return return_string + "{}\t{}".format(self.name, self.privs)

class SudoerAuditor:

    sudoers_file = ""
    sudoers = []
    include_dirs = []
    recs = []
    changed_sudoers_file = False

    def run(self):
        self.backup_sudoers()
        self.read_sudoers()
        self.parse_sudoers()
        self.audit_sudoers()

        if self.changed_sudoers_file:
            self.write_sudoers_file()

    def backup_sudoers(self):
        now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        run(["sudo", "cp", "/etc/sudoers", "/etc/sudoers.{}.bkp".format(now)],
            capture_output=True, text=True)

        print("Backup created at /etc/sudoers.{}.bkp".format(now))


    def read_sudoers(self):
        process = run(["sudo", "cat", "/etc/sudoers"],
                      capture_output=True, text=True)

        self.sudoers_file = process.stdout.strip()

    def parse_sudoers(self):
        lines = self.sudoers_file.splitlines()

        for line in lines:
            line = line.strip()

            if "#includedir" in line or "@includedir" in line:
                self.include_dirs.append(line.split(" ", 1)[1])
                continue

            elif line == "" or "#" in line or "Defaults" in line:
                continue

            sudoer = Sudoer()

            if "%" in line:
                sudoer.type = SudoerType.GROUP

            else:
                sudoer.type = SudoerType.USER

            sudoer.name, sudoer.privs = line.replace("%", "").split("\t", 1)

            self.sudoers.append(sudoer)

    def audit_sudoers(self):
        for sudoer in self.sudoers:
            print()
            self.audit_sudoer(sudoer)

    def audit_sudoer(self, sudoer: Sudoer):
        default = False
        if sudoer.name in ["root", "sudo", "wheel", "admin"]:
            print("Please note that '{}'".format(sudoer.name),
                  "is a default {} in some distros!".format(sudoer.type))
            default = True

        prompt = "Should '{}' {} ".format(sudoer.name, sudoer.type)
        prompt += "have '{}' privileges?".format(sudoer.privs)
        privileged = get_yes_or_no(prompt, True)

        if privileged:
            if sudoer.type == SudoerType.GROUP:
                self.audit_group_users(sudoer)
            return

        elif not privileged and default:
            print("Since '{}' is a default {}".format(sudoer.name, sudoer.type),
                  "please manually correct its permissions")
            self.recs.append("Correct sudoer privileges: {}".format(sudoer))
            return

        # else
        prompt = "Would you like to remove sudo privileges "
        prompt += "from the '{}' {}?".format(sudoer.name, sudoer.type)
        remove = get_yes_or_no(prompt, False)

        if remove:
            self.remove_sudoer(sudoer)

        else:
            print("Please manually correct {}'s permissions".format(sudoer.name))
            self.recs.append("Correct sudoer privileges: {}".format(sudoer))

    def audit_group_users(self, group: Sudoer):
        process = run(["getent", "group", group.name], capture_output=True, text=True)
        group_line = process.stdout.strip()

        if group_line == "":
            print("Group '{}' wasn't found".format(group.name))
            return

        users = group_line.split(":")[3].split(",")

        for user in users:
            self.audit_group_user(group, user)


    def audit_group_user(self, group: Sudoer, user: str):
        current_user = False
        if user == getuser():
            current_user = True
            print("Please note that you are currently user '{}'!".format(user))
        prompt = "Should '{user}' be part of sudoer group '{}'?".format(group.name)
        part_group = get_yes_or_no(prompt, True)

        if part_group:
            return

        if not part_group and current_user:
            print("Please manually remove self ({})".format(user),
                  "from sudoer group '{}'".format(group.name))
            rec = "DANGEROUS! Remove self ({}) ".format(user)
            rec += "from sudoer group '{}'".format(group.name)
            self.recs.append(rec)
            return


        prompt = "Would you like to remove '{}' ".format(user)
        prompt += "from sudoer group '{}'?".format(group.name)

        remove = get_yes_or_no(prompt, False)

        if remove:
            self.remove_user_from_group(user, group)

        else:
            print("Please manually remove '{}'",
                  "from sudoer group '{}'")
            rec = "Remove '{}' from sudoer group '{}'".format(user, group.name)
            self.recs.append(rec)


    def remove_sudoer(self, sudoer: Sudoer):
        self.changed_sudoers_file = True

        self.sudoers_file = self.sudoers_file.replace(str(sudoer), "")

    def remove_user_from_group(self, user: str, group: Sudoer):
        process = run(["sudo", "gpasswd", "-d", user, group.name],
                      stdout=DEVNULL, stderr=DEVNULL)

        if process.returncode == 0:
            s = "Successfully removed '{}' from sudoer group '{}'".format(
                user, group.name)
            print(s)

        else:
            print("Failed to remove '{}' from sudoer group '{}'".format(
                user, group.name
            ))
            print("Please manually remove '{}'".format(user),
                  "from sudoer group '{}'".format(group.name))
            self.recs.append("Remove {} from sudoer group {}".format(
                user, group.name))

    def write_sudoers_file(self):
        tmp_sudoers_path = "/tmp/sudoers"
        sudoers_path = "/etc/sudoers"
        with open(tmp_sudoers_path, "w") as outfile:
            outfile.write(self.sudoers_file)

        process = run(["visudo", "-c", "-f", tmp_sudoers_path],
                      stdout=DEVNULL, stderr=DEVNULL)

        if process.returncode != 0:
            print("Failed 'visudo' checks, please make changes manually")
            remove(tmp_sudoers_path)
            return

        process = run(["sudo", "cp", tmp_sudoers_path, sudoers_path])

        if process.returncode != 0:
            print("Failed to write changes to '{}',".format(sudoers_path),
                  "please make changes manually")
            remove(tmp_sudoers_path)
            return

        remove(tmp_sudoers_path)
        print("Successfully edited '/etc/sudoers'")

