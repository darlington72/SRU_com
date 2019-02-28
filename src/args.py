import argparse
import version

# Args parser
parser = argparse.ArgumentParser(
    description="SRU Com " + version.__version__, prog="SRU_com"
)
parser.add_argument(
    "--version", action="version", version="%(prog)s " + version.__version__
)
parser.add_argument(
    "-f",
    "--file",
    help="Write output to file",
    metavar="FILE_NAME",
    nargs="?",
    const="output",
)
parser.add_argument(
    "-w",
    "--watchdog",
    action="store_true",
    help="Set the watchdog to be cleared on startup",
)
parser.add_argument("-v", dest="verbose", action="store_true", help="Verbose mode")
parser.add_argument(
    "-t",
    "--test",
    action="store_true",
    help="Start in test mode (serial loop simulation)",
)
parser.add_argument("-l", "--loop", action="store_true", help="Serial loop mode")
parser.add_argument(
    "-U", "--update", dest="update", action="store_true", help="Update SRU_com "
)
parser.add_argument(
    "-s",
    "--scenario",
    help="Load a scenario on startup",
    metavar="FILE_NAME",
    nargs="?",
    const="output",
)
args = parser.parse_args()
