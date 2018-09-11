from version import __version__


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
    print_c(f"Current version {__version__}, looking for update..", "info")

