# Table of Contents

1. [Description](#payme)
2. [Screenshots](#screenshots)
    1. [Autofilled Venmo Request](#autofilled-venmo-request)
3. [How-Tos](#how-tos)
    1. [Run](#run)
    2. [Host](#host)

# PayMe
Just a simple repo to calculate how much to request from people after a night out

# Screenshots

# How tos
## Run

1. Clone the repository:
```
git clone https://github.com/pomkos/payme
cd payme
```

2. Create a conda environment (optional):

```
conda create --name "pay_env"
```

3. Activate environment, install python, install dependencies.

```
conda activate pay_env
conda install python=3.8
pip install -r requirements.txt
```
3. Start the application:
```
streamlit run payme.py
```
5. Access the application at `localhost:8501`

## Host

1. Create a new file outside the `payme` directory:

```
cd
nano payme.sh
```

2. Paste the following in it, then save and exit:

```
#!/bin/bash

source ~/anaconda3/etc/profile.d/conda.sh

cd ~/payme
conda activate pay_env

nohup streamlit run payme.py --server.port 8503 &
```

3. Edit crontab so portfolio is started when server reboots

```
crontab -e
```

4. Add the following to the end, then save and exit

```
@reboot /home/payme.sh --server.port 8503
```

5. Access the website at `localhost:8503`
