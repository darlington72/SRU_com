"""args.py

Compute every flags passed to SRU_com on startup into the args object
"""

import argparse
import version

# Args parser
parser = argparse.ArgumentParser(
    description="SRU Communication Software V" + version.__version__, prog="SRU_com"
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

test_group = parser.add_argument_group("Test / Simulation")

test_group.add_argument(
    "-t",
    "--test",
    action="store_true",
    help="Start in test mode (no UART nor SRU needed)",
)
test_group.add_argument("-l", "--loop", action="store_true", help="Serial loop mode (TX -> RX: no SRU needed)")

parser.add_argument(
    "-U", "--update", dest="update", action="store_true", help="Update SRU_com "
)

scenario_group = parser.add_argument_group("Scenario Mode")

scenario_group.add_argument(
    "-s",
    "--scenario",
    help="Load a scenario on startup",
    metavar="FILE_NAME",
    nargs="?",
    const="output",
)
scenario_group.add_argument(
    "-q",
    "--quit_after_scenario",
    action="store_true",
    help="Quit SRU_com after scenario is played",
)
scenario_group.add_argument(
    "--check_only", action="store_true", help="Check scenario syntax only"
)

socket_group = parser.add_argument_group("Socket Mode")

socket_group.add_argument("-S", "--socket", action="store_true", help="Start in socket mode")
socket_group.add_argument("--without_encapsulation", action="store_true", help="Don't encapsulate the data")
socket_group.add_argument("--localhost", action="store_true", help="Start socket on localhost (test purpose)")




args = parser.parse_args()
