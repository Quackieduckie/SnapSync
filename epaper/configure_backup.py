#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path

def get_input(prompt, default=None):
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()

def create_backup_script(config):
    script_content = f"""#!/bin/bash

# Backup Configuration
BACKUP_SOURCES={json.dumps(config['backup_sources'])}
BK0_PATH="{config['bk0_path']}"
BK1_PATH="{config['bk1_path']}"
STATUS_FILE="{config['status_file']}"

RSYNC_OPTS="-aAXv --delete --numeric-ids --exclude={{'/dev/*','/proc/*','/sys/*','/tmp/*','/run/*','/mnt/*','/media/*','/lost+found'}}"

update_status() {{
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" > "$STATUS_FILE"
}}

update_status "Starting backup"

for source in "${{!BACKUP_SOURCES[@]}}"; do
    source_config="${{BACKUP_SOURCES[$source]}}"
    echo "Backing up $source..."
    rsync $RSYNC_OPTS -e "ssh -p ${{source_config['port']}}" --rsync-path="sudo rsync" "${{source_config['user']}}@${{source_config['host']}}:${{source_config['path']}}" "$BK0_PATH/${{source_config['backup_dir']}}/"
    
    if [ $? -ne 0 ]; then
        echo "$source backup failed!"
        update_status "$source failed"
        exit 1
    fi
done

update_status "BK0 done"

read -p "Update BK1? [y/N]: " confirm_bk1

if [[ "$confirm_bk1" =~ ^[Yy]$ ]]; then
    echo "Remounting BK1 rw..."
    sudo mount -o remount,rw "$BK1_PATH"

    echo "Syncing BK0 → BK1..."
    rsync -av --delete "$BK0_PATH/" "$BK1_PATH/"

    if [ $? -eq 0 ]; then
        echo "BK1 done"
        update_status "BK1 done"
    else
        echo "BK1 failed!"
        update_status "BK1 failed"
    fi

    echo "Remounting BK1 ro..."
    sudo mount -o remount,ro "$BK1_PATH"
else
    echo "BK1 skipped"
fi

update_status "Backup done"
"""
    
    with open('backup.sh', 'w') as f:
        f.write(script_content)
    
    # Make the script executable
    os.chmod('backup.sh', 0o755)

def main():
    print("SnapSync Backup Configuration")
    print("===========================")
    
    config = {
        'backup_sources': {},
        'bk0_path': get_input("Enter BK0 path", "/mnt/nvme0"),
        'bk1_path': get_input("Enter BK1 path", "/mnt/nvme1"),
        'status_file': get_input("Enter status file path", "/home/pi/backup_status.txt")
    }
    
    while True:
        print("\nAdd backup source (or press Enter to finish)")
        source_name = get_input("Source name (e.g., server1)")
        if not source_name:
            break
            
        source_config = {
            'user': get_input("Username"),
            'host': get_input("Hostname/IP"),
            'port': get_input("SSH port", "22"),
            'path': get_input("Source path", "/"),
            'backup_dir': get_input("Backup directory name", source_name)
        }
        
        config['backup_sources'][source_name] = source_config
    
    if not config['backup_sources']:
        print("No backup sources configured. Exiting.")
        sys.exit(1)
    
    print("\nConfiguration complete. Generating backup script...")
    create_backup_script(config)
    print("Backup script generated as 'backup.sh'")
    print("\nNext steps:")
    print("1. Review backup.sh")
    print("2. Set up SSH keys for remote servers")
    print("3. Run backup.sh manually or set up a cron job")

if __name__ == "__main__":
    main() 