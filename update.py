import requests
import json
from pprint import pprint
import sys
import tarfile
from tqdm import tqdm
from time import sleep


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
    print_c(f"Current version {__version__}, looking for update at {REPO}", "run")

    r = requests.get(REPO, headers={"Accept-Encoding": "identity"})

    if r.ok:
        response = json.loads(r.text or r.content)

        last_version_name = response["tag_name"]
        last_version_url = response["tarball_url"]

        if last_version_name > __version__:
            print_c(f"New version {last_version_name} available !", "good")
            # print_c("", "run")

            # pprint(response)
            r = requests.get(
                last_version_url, stream=True, headers={"Accept-Encoding": "identity"}
            )

            # pprint(r.headers)

            if r.status_code == 200:
                last_version_name += ".tar.gz"
                with open(last_version_name, "wb") as f:
                    size_downloaded = 0
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
                            total=total_size,
                            ncols=100,
                            desc="\033[97m[~]\033[0m Downloading new version.. ",
                        ) as pbar:
                            for chunk in r.iter_content(
                                chunk_size=int(int(total_size or 400000) / 100)
                            ):
                                f.write(chunk)
                                pbar.update(1)
                    print_c(f"Release downloaded <{last_version_name}>", "good")

                    print_c("Decompressing..", "run", False)

                    # print(tarfile.is_tarfile(last_version_name))
                    tar_release = tarfile.open(last_version_name, mode="r:gz")
                    tar_release.extractall()

                    print(" Done.")

        else:
            print_c("SRU_com is already up to date", "good")
            sys.exit(0)

