import requests
import json
from pprint import pprint
import sys

from version import __version__

__version__ = "0.1.1"

# https://api.github.com/repos/superlevure/SRU_com/releases/latest

REPO = "https://api.github.com/repos/superlevure/SRU_com/releases/latest"

COMMANDS = {
    # Lables
    "info": (33, "[!] "),
    "que": (34, "[?] "),
    "bad": (31, "[-] "),
    "good": (32, "[+] "),
    "run": (97, "[~] "),
}


def print_c(string, message_type):
    """print_colored
    """
    print(
        "\033[{}m{}\033[0m{}".format(
            COMMANDS[message_type][0], COMMANDS[message_type][1], string
        )
    )


def update():
    print_c("Welcome to SRU_com update.", "info")
    print_c(f"Current version {__version__}, looking for update at {REPO}", "run")

    r = requests.get(REPO)
    if r.ok:
        response = json.loads(r.text or r.content)
        last_version_name = response["tag_name"]
        last_version_url = response["tarball_url"]

        if last_version_name > __version__:
            print_c(f"New version {last_version_name} avalaible !", "good")
            print_c("Downloading new version..", "run")

            # pprint(response)
            r = requests.get(
                last_version_url, stream=True, headers={"Accept-Encoding": "identity"}
            )

            pprint(r.headers)

            if r.status_code == 200:
                with open(last_version_name, "wb") as f:
                    size_downloaded = 0
                    total_size = r.headers["Content-Length"]

                    for chunk in r:
                        f.write(chunk)
                        size_downloaded += 128
                        print(f"{size_downloaded} /  {total_size}")
        else:
            print_c("SRU_com is already up to date", "bad")
            sys.exit(0)

