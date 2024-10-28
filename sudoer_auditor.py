from enum import Enum
from subprocess import DEVNULL, run
from input_gatherer import get_yes_or_no
from getpass import getuser
from datetime import datetime
from os import remove

class SudoerType(Enum):
    USER = 0
    GROUP = 1

    def __str__(self):
        if self == SudoerType.USER:
            return "user"
        else:
            return "group"

class Sudoer:
    name: str
    type: SudoerType
    privs: str

    def __str__(self) -> str:
        return_string = ""
        if self.type == SudoerType.GROUP:
            return_string += "%"

        return return_string + f"{self.name}\t{self.privs}"

class SudoerAuditor:

    sudoers_file: str = ""
    sudoers: list[Sudoer] = []
    include_dirs: list[str] = []
    recs: list[str] = []
    changed_sudoers_file: bool = False

    def run(self):
        self.backup_sudoers()
        self.read_sudoers()
        self.parse_sudoers()
        self.audit_sudoers()

        if self.changed_sudoers_file:
            self.write_sudoers_file()

    def backup_sudoers(self):
        now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        run(["sudo", "cp", "/etc/sudoers", f"/etc/sudoers.{now}.bkp"],
            capture_output=True, text=True)

        print(f"Backup created at /etc/sudoers.{now}.bkp")


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
            print(f"Please note that '{sudoer.name}'",
                  f"is a default {sudoer.type} in some distros!")
            default = True

        prompt = f"Should '{sudoer.name}' {sudoer.type} "
        prompt += f"have '{sudoer.privs}' privileges?"
        privileged = get_yes_or_no(prompt, True)

        if privileged:
            if sudoer.type == SudoerType.GROUP:
                self.audit_group_users(sudoer)
            return

        elif not privileged and default:
            print(f"Since '{sudoer.name}' is a default {sudoer.type}",
                  "please manually correct its permissions")
            self.recs.append(f"Correct sudoer privileges: {sudoer}")
            return

        # else
        prompt = f"Would you like to remove sudo privileges "
        prompt += f"from the '{sudoer.name}' {sudoer.type}?"
        remove = get_yes_or_no(prompt, False)

        if remove:
            self.remove_sudoer(sudoer)

        else:
            print(f"Please manually correct {sudoer.name}'s permissions")
            self.recs.append(f"Correct sudoer privileges: {sudoer}")

    def audit_group_users(self, group: Sudoer):
        process = run(["getent", "group", group.name], capture_output=True, text=True)
        group_line = process.stdout.strip()

        if group_line == "":
            print(f"Group '{group.name}' wasn't found")
            return

        users: list[str] = group_line.split(":")[3].split(",")

        for user in users:
            self.audit_group_user(group, user)


    def audit_group_user(self, group: Sudoer, user: str):
        current_user: bool = False
        if user == getuser():
            current_user = True
            print(f"Please note that you are currently user '{user}'!")
        prompt = f"Should '{user}' be part of sudoer group '{group.name}'?"
        part_group = get_yes_or_no(prompt, True)

        if part_group:
            return

        if not part_group and current_user:
            print(f"Please manually remove self ({user})",
                  f"from sudoer group '{group.name}'")
            rec = f"DANGEROUS! Remove self ({user}) "
            rec += f"from sudoer group '{group.name}'"
            self.recs.append(rec)
            return


        prompt = f"Would you like to remove '{user}' "
        prompt += f"from sudoer group '{group.name}'?"

        remove = get_yes_or_no(prompt, False)

        if remove:
            self.remove_user_from_group(user, group)

        else:
            print(f"Please manually remove '{user}'",
                  f"from sudoer group '{group.name}'")
            self.recs.append(f"Remove '{user}' from sudoer group '{group.name}'")


    def remove_sudoer(self, sudoer: Sudoer):
        self.changed_sudoers_file = True

        self.sudoers_file = self.sudoers_file.replace(str(sudoer) + "\n", "")

    def remove_user_from_group(self, user: str, group: Sudoer):
        process = run(["sudo", "gpasswd", "-d", user, group.name])

        if process.returncode == 0:
            print(f"Successfully removed '{user}' from sudoer group '{group.name}'")

        else:
            print(f"Failed to remove '{user}' from sudoer group '{group.name}'")
            print(f"Please manually remove '{user}'",
                  f"from sudoer group '{group.name}'")
            self.recs.append(f"Remove {user} from sudoer group {group.name}")

    def write_sudoers_file(self):
        tmp_sudoers_path = "/tmp/sudoers"
        sudoers_path = "/etc/sudoers"
        with open(tmp_sudoers_path, "w") as outfile:
            outfile.write(self.sudoers_file)

        process = run(["visudo", "-c", "-f", tmp_sudoers_path], stdout=DEVNULL)

        if process.returncode != 0:
            print("Failed 'visudo' checks, please make changes manually")
            remove(tmp_sudoers_path)
            return

        process = run(["sudo", "cp", tmp_sudoers_path, sudoers_path])

        if process.returncode != 0:
            print(f"Failed to write changes to '{sudoers_path}',",
                  "please make changes manually")
            remove(tmp_sudoers_path)
            return

        remove(tmp_sudoers_path)
        print("Successfully edited '/etc/sudoers'")

