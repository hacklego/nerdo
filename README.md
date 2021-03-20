# nerdo
NEwly Registered DOmains: a tool to find suspicious domains.

# Installation

From pypi:

```
pip3 install nerdo
```

From repo:

```
git clone https://github.com/hacklego/nerdo.git
cd nerdo
pip3 install .
```

## Usage
```
usage: nerdo [-h] [-v] [keywords [keywords ...]]

positional arguments:
  keywords       string or file with keywords to look for in the newly
                 registered domains. If none then stdin will be use

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Verbosity mode
```

## Example
```
nerdo google
low googlemasti.xyz
low wwwgoogle2a.xyz
```
