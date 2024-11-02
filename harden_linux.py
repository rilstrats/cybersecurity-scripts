#!/usr/bin/env python3

from system_updater import SystemUpdater
from sudoer_auditor import SudoerAuditor
from ssh_configurer import SSHConfigurer

def main():
    statement = "System Update"
    print("#" * (len(statement) + 4))
    print("# " + statement + " #")
    print("#" * (len(statement) + 4))
    print()
    updater = SystemUpdater()
    updater.run()

    statement = "Sudoer Audit"
    print("#" * (len(statement) + 4))
    print("# " + statement + " #")
    print("#" * (len(statement) + 4))
    print()
    sudoer_auditor = SudoerAuditor()
    sudoer_auditor.run()

    statement = "SSH Configuration"
    print("#" * (len(statement) + 4))
    print("# " + statement + " #")
    print("#" * (len(statement) + 4))
    print()
    ssh_configurer = SSHConfigurer()
    ssh_configurer.run()

if __name__ == "__main__":
    main()
