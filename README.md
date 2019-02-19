# Usage

```
usage: SRU_com [-h] [--version] [-f [FILE_NAME]] [-w] [-v] [-t] [-U]

SRU Com 1.5.3

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -f [FILE_NAME], --file [FILE_NAME]
                        Write output to file
  -w, --watchdog        Set the watchdog to be cleared on startup
  -v                    Verbose mode
  -t, --test            Start in test mode (serial loop simulation)
  -U, --update          Update SRU_com (BETA)
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



