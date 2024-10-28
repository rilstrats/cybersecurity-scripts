#!/bin/python3

from system_updater import SystemUpdater
from sudoer_auditor import SudoerAuditor

def main():
    # updater = SystemUpdater()
    # updater.update()
    sudoer_auditor = SudoerAuditor()
    sudoer_auditor.run()

if __name__ == "__main__":
    main()
