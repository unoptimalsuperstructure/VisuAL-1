# Installation Guide

If you are running the py file by cloning the repo, this is VisuAL-1 installation guide for reference

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
## Steps
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

### 3. Start MongoDB

For Linux based OS, run the code below. The second line is to check your MongoDB connection
```
sudo systemctl start mongodb
sudo systemctl status mongodb
```

### 4. Run the app

```bash
python Main.py
```

## Compatibility issues

- When running Main.py on flatpak / snap installed vscode, opening 3d rendering will crash. As such please run `python3 Main.py` on your own terminal instead. 
    
    I have not tested AUR maintained vscode, if it runs into the same issue, just follow whatever mentioned

- For any Linux 6.19+ kernel users, note that mongodb will crash, the work around is to run `sudo systemctl edit mongodb.service` and edit `Environment="GLIBC_TUNABLES=glibc.pthread.rseq=0"` to `Environment="GLIBC_TUNABLES=glibc.pthread.rseq=1"` 

    - If it shows this
        ```bash
        [hehehe@archlinux VisuAL-1]$ sudo systemctl edit mongodb
        /etc/systemd/system/mongodb.service.d/override.conf: after editing, new contents are empty, not writing file.
        ```
        run this to fix it
        ```
        sudo mkdir -p /etc/systemd/system/mongodb.service.d
        sudo tee /etc/systemd/system/mongodb.service.d/override.conf << 'EOF'
        [Service]
        Environment="GLIBC_TUNABLES=glibc.pthread.rseq=1"
        EOF
        ```
    Afterward, run 
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl restart mongodb
    sudo systemctl status mongodb
    ```