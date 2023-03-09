# Crafty-Client

## About

Crafty Client is a pypi (pip) package for interfacing with the [Crafty Web MC server control panel](https://gitlab.com/crafty-controller/crafty-4).

It was written from scratch and is based on requests.

## Install
## CRAFTY CLIENT IS NOT READY FOR INSTALL VIA PIP YET
<!---
Make sure you have python3 installed on your system with the pip package manager.

#### For windows (conda) environments
```bash
pip install crafty-client
```

#### For linux (apt/yum/rpm/etc.) environments
```bash
pip3 install crafty-client
```
--->
## Usage

Example:
```python
from crafty_client import CraftyWeb

URL = "https://127.0.0.1:8000"    # The location of the crafty-web webserver
API_TOKEN = "<place token here>"  # Your crafty Web API token, printed in the console at installation.

crafty = CraftyWeb(URL, API_TOKEN)

print(crafty.get_all_servers())
```
