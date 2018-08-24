import argparse
import version

# Args parser
parser = argparse.ArgumentParser(
    description="SRU Com " + version.__version__, prog="SRU_com"
)
parser.add_argument("-l", "--loop", action="store_true", help="Serial loop mode")
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
args = parser.parse_args()
