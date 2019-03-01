from src.lib import BD_TC


def parse_scenario(scenario_file):
    """Scenario parser 

    Arguments:
        scenario_file {[str]} -- Scenario file

    Raises:
        ValueError -- Invalid keyword 
        ValueError -- Argument number (wait)
        ValueError -- Argument type: int (wait)
        ValueError -- Argument type: hex (send)
        ValueError -- TC present in BD
        ValueError -- Argument missing (send)
        ValueError -- Argument too long (send)

    Returns:
        [list] -- Scenario that can be exploited by serial_com.play_scenario()
    """

    KEYWORDS = ("send", "wait", "//")

    ex = [
        {"keyword": "send", "argument": "TC-88"},
        {"keyword": "send", "argument": "TC-88 FF, AA"},
    ]

    # Delete whitespace, trailing space etc
    scenario_file = scenario_file.strip()

    # List
    scenario_list = scenario_file.split("\n")

    # Delete whitespace, trailing space for
    # each element of the list this time
    scenario_list = list(map(str.strip, scenario_list))

    scenario = []
    for element in scenario_list:
        try:
            keyword, argument = element.split(" ", maxsplit=1)
        except ValueError:
            raise ValueError(f'Missing argument after keyword "{element}"')

        if keyword not in KEYWORDS:
            raise ValueError(f'Invalid keyword "{keyword}"')

        # If line is a comment
        if keyword == "//":
            scenario.append({"keyword": "//", "comment": argument})

        #### Syntax verification

        elif keyword == "wait":
            if len(argument.split(" ")) != 1:
                raise ValueError(f'Need exactly one argument "{argument}"')
            else:
                argument = argument.strip("s")

                try:
                    argument = int(argument)
                except ValueError:
                    raise ValueError(f'Argument must be an int "{argument}""')

            scenario.append({"keyword": keyword, "argument": argument})

        elif keyword == "send":
            scenario_TC_tag, *scenario_TC_args = argument.split(" ", maxsplit=1)

            if len(scenario_TC_args) > 0:
                scenario_TC_args = scenario_TC_args[0].split(",")
                scenario_TC_args = list(map(str.strip, scenario_TC_args))

                # Check if arguments are all hex
                try:
                    list(map(lambda x: int(x, 16), scenario_TC_args))
                except ValueError:
                    raise ValueError(
                        f'Non hexadecimal value in args "{scenario_TC_args}"'
                    )

            # Check if the TC exits
            try:
                TC = BD_TC[scenario_TC_tag]
            except KeyError:
                raise ValueError(f'TC does not exist in BD "{scenario_TC_tag}"')
            else:

                # Check if each TC_args has an argument in the scenario
                # Check also argument length
                argument_pointer = 0
                for BD_TC_args in TC["data"]:
                    try:
                        param_size = int(BD_TC_args[0])
                        param_name = BD_TC_args[1]
                        param_value = BD_TC_args[2]
                    except (IndexError, ValueError):
                        pass
                    else:

                        if param_value == "?":

                            try:
                                scenario_TC_arg = (
                                    scenario_TC_args[argument_pointer]
                                    .zfill(2 * param_size)
                                    .upper()
                                )
                            except IndexError:
                                raise ValueError(
                                    f'Missing value for parameter "{param_name}" of {scenario_TC_tag}'
                                )
                            else:
                                if len(scenario_TC_arg) > 2 * param_size:
                                    raise ValueError(
                                        f'Argument too long "{scenario_TC_arg}"'
                                    )

                        argument_pointer += 1

            scenario.append(
                {
                    "keyword": keyword,
                    "TC_tag": scenario_TC_tag,
                    "TC_args": scenario_TC_args,
                }
            )

    return scenario


if __name__ == "__main__":
    import json
    import sys

    try:

        BD_TM_file = open("BD/BDTM.json", "r")
        BD_TM = json.load(BD_TM_file)
    except FileNotFoundError:
        print("BDTM file not found.")
        sys.exit()

    try:
        BD_TC_file = open("BD/BDTC.json", "r")
        BD_TC = json.load(BD_TC_file)
    except FileNotFoundError:
        print("BDTC file not found.")
        sys.exit()

    with open("scenario.txt", "r") as f:
        scenario_file = f.read()

        parse_scenario(scenario_file)
