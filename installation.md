# Installation Guide

This is VisuAL-1 installation guide for reference

## Pre-req

Ensure you have the following:

- Python 3.8 or higher
- pip
- MongoDB

Optionally, have Git installed

To install pip and git,

- Debian based OS,

```bash
sudo apt update && sudo apt upgrade
sudo apt install pip git 
```

- For Arch based OS,

```bash
sudo pacman -Syu
sudo pacman -S pip git
```

For all users except Arch, refer to [MongoDB Community Edition Installation Guide](https://www.mongodb.com/docs/v7.0/administration/install-community/) for MongoDB installation 

For Arch users, use paru or yay to install mongodb or mongodb-bin. E.g

```bash
paru -S mongodb-bin
```

### 1. Clone the repo

If you do not have git, download the repo as a zip file 

If you have git, run 

```bash
git clone https://github.com/unoptimalsuperstructure/VisuAL-1.git
cd VisuAL-1
```

### 2. Install pip dependencies

<b>Note: If you are using MacOS or any Linux based OS, create a venv if you don't have it</b>

```bash
python -m venv .venv
. .venv/bin/activate
```

To install pip modules, run (rmb to activate venv if needed)

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
python Main.py
```