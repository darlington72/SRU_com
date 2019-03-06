""" update.py

Update routine of SRU_com 
"""
from distutils.dir_util import copy_tree
from pathlib import Path
import json
import sys
import tarfile
from datetime import datetime
import os
import shutil
from tqdm import tqdm
import requests
import sys
from version import __version__


REPO = "https://api.github.com/repos/superlevure/SRU_com/releases/latest"
FILE_TO_BACKUP = ('SRU_com/', 'README.md')
COMMANDS = {
    # Labels
    "info": (33, "[!] "),
    "que": (34, "[?] "),
    "bad": (31, "[-] "),
    "good": (32, "[+] "),
    "run": (97, "[~] "),
}

CURRENT_DIR = Path(sys.path[0]).parent



def print_c(string, message_type, endline=True):
    """print_colored
    """
    print(
        "\033[{}m{}\033[0m{}".format(
            COMMANDS[message_type][0], COMMANDS[message_type][1], string
        ),
        end=("\n" if endline else ""),
    )


def update():
    print_c("Welcome to SRU_com update.", "info")
    print_c(f"Current dir: {CURRENT_DIR}", "info")
    print_c(f"Current version {__version__}, looking for update at {REPO}", "run")

    try:
        r = requests.get(REPO, headers={"Accept-Encoding": "identity"})

        if r.ok:
            response = json.loads(r.text or r.content)

            last_version_name = response["tag_name"]
            last_version_url = response["tarball_url"]

            if last_version_name > __version__:
                print_c(
                    f"New version {last_version_name} is available at {last_version_url} !",
                    "good",
                )

                print_c("Backing up current version to tar file..", "run")

                backup_dir = "../backups"
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                current_date = datetime.now().strftime("%Y-%m-%d")
                backup_name = "SRU_com-" + __version__ + "-" + current_date + ".tar.gz"

                with tarfile.open(
                    backup_dir + "/" + backup_name, mode="w:gz"
                ) as backup:
                    for file in FILE_TO_BACKUP:
                        print_c(f'Backinp up "{file}"..', "run")
                        backup.add(
                            str(CURRENT_DIR) + "/" + file,
                            recursive=True,
                            arcname=os.path.basename(CURRENT_DIR) + file
                        )

                print_c(
                    f"SRU_com has been backed up to {backup_dir}/{backup_name}", "good"
                )

                print_c(f"Downloading new version..", "run")

                r = requests.get(
                    last_version_url,
                    stream=True,
                    headers={"Accept-Encoding": "identity"},
                )

                if r.status_code == 200:
                    last_version_name += ".tar.gz"
                    with open(last_version_name, "wb") as f:
                        try:
                            total_size = r.headers["Content-Length"]
                        except KeyError:
                            print_c("Release length unavailable", "info")
                            total_size = None

                        if total_size is None:
                            for chunk in r:
                                f.write(chunk)
                        else:
                            with tqdm(
                                total=100, ncols=100, desc="\033[97m[~]\033[0m "
                            ) as pbar:
                                for chunk in r.iter_content(
                                    chunk_size=int(int(total_size) / 99)
                                ):
                                    f.write(chunk)
                                    pbar.update(1)

                    print_c(f"Release downloaded <{last_version_name}>", "good")

                    print_c("Decompressing..", "run", False)
                    tar_release = tarfile.open(last_version_name)
                    tar_release.extractall()
                    tar_release_name = tar_release.getnames()[0]
                    print(" Done.")

                    print_c("Installing new version..", "run", endline=False)
                    copy_tree(tar_release_name + "/", str(CURRENT_DIR) + "/")
                    print(" Done.")

                    print_c("Deleting temporary files..", "run", endline=False)
                    os.remove(tar_release.name)
                    shutil.rmtree(tar_release_name)
                    print(" Done.")

                    print_c(
                        f"New version {last_version_name} has been installed !", "good"
                    )

                else:
                    print_c(
                        "Error in HTTP request, please check the connection and try again.",
                        "bad",
                    )
                    sys.exit(0)
            else:
                print_c("SRU_com is already up to date", "good")
                sys.exit(0)

        else:
            print_c(
                "Error in HTTP request, please check the connection and try again.",
                "bad",
            )
            sys.exit(0)

    except requests.exceptions.ConnectionError:
        print_c("Failed to connect, please check the connection and try again.", "bad")
        sys.exit(0)


# update()
