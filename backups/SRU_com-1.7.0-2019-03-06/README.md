# Usage

```
usage: SRU_com [-h] [--version] [-f [FILE_NAME]] [-w] [-v] [-t] [-l] [-U]
               [-s [FILE_NAME]] [-q] [--check_only] [-S]

SRU Communication Software V1.7.1

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -f [FILE_NAME], --file [FILE_NAME]
                        Write output to file
  -w, --watchdog        Set the watchdog to be cleared on startup
  -v                    Verbose mode
  -U, --update          Update SRU_com
  -S, --socket          Start in socket mode

Test / Simulation:
  -t, --test            Start in test mode (no UART nor SRU needed)
  -l, --loop            Serial loop mode (TX -> RX: no SRU needed)

Scenario Mode:
  -s [FILE_NAME], --scenario [FILE_NAME]
                        Load a scenario on startup
  -q, --quit_after_scenario
                        Quit SRU_com after scenario is played
  --check_only          Check scenario syntax only
```


## Prerequisites 
```
python >= 3.6
```

## Todo on first install: 
#### Clone the repo
```
git clone https://github.com/superlevure/SRU_com
cd SRU_com
```

#### Create the virtual environnement
```
python3 -m venv .env
```
#### Activate the virtual environnement
```
source .env/bin/activate (on Unix) 
.env/Scripts/activate.bat (on Windows) 
```

#### Install the requirements 
```
pip install -r requirements.txt
```


## To launch the script : 
#### Activate the virtual environnement
```
source .env/bin/activate (on Unix) 
.env/Scripts/activate.bat (on Windows) 
```
#### Launch SRU_com
```
python SRU_com.py
```



