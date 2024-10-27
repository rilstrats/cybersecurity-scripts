from enum import Enum
from subprocess import run

class Distro(Enum):
    OTHER = 0
    DEBIAN = 1
    FEDORA = 2

class SystemUpdater:

    os_release: dict[str, str] = {}
    distro: Distro = Distro.OTHER


    def __init__(self):
        self.get_os_release()
        self.determine_distro()

    def get_os_release(self):
        with open("/etc/os-release") as infile:
            os_release_lines = infile.readlines()

        for line in os_release_lines:
            line = line.strip()
            if line == "" or "=" not in line:
                continue

            key, value = line.split("=", 1)
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]

            self.os_release[key] = value

    def determine_distro(self):
        os_ids: list[str | None] = [
            self.os_release.get("ID"),
            self.os_release.get("ID_LIKE")
        ]

        for os_id in os_ids:
            if os_id == "fedora":
                self.distro = Distro.FEDORA
                return
            elif os_id == "debian":
                self.distro = Distro.DEBIAN
                return

        self.distro = Distro.OTHER

    def update(self):
        if self.distro == Distro.OTHER:
            print("Unsupported distro, please update manually")
        elif self.distro == Distro.FEDORA:
            self.update_fedora()
        elif self.distro == Distro.DEBIAN:
            self.update_debian()

    def update_fedora(self):
        process = run(["sudo", "dnf", "upgrade", "-y"])
        if process.returncode != 0:
            print("Error running 'dnf upgrade'")
            return

        print("Successfully updated using 'dnf'")


    def update_debian(self):
        process = run(["sudo", "apt-get", "update", "-y"])
        if process.returncode != 0:
            print("Error running 'apt update'")
            return

        process = run(["sudo", "apt-get", "upgrade", "-y"])
        if process.returncode != 0:
            print("Error running 'apt upgrade'")
            return

        print("Successfully updated with 'apt'")


