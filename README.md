# Table of Contents

1. [Description](#payme)
2. [Screenshots](#screenshots)
    1. [OCR Mode](#ocr-mode)
    1. [Autofilled Venmo Request](#autofilled-venmo-request)
    2. [Default View with Inputs](#default-view-with-inputs)
    3. [Default View without Inputs](#default-view-without-inputs)
    4. [Expanded Page](#expanded-page)
    5. [Database Outline](#postgres-database-outline)
3. [How-Tos](#how-tos)
    1. [Run](#run)
    2. [Host](#host)

# PayMe
Just a simple repo to calculate how much to request from people after a night out

# Screenshots

## OCR Mode
<img src="https://github.com/pomkos/payme/blob/main/images/venmo-auto.png" width="620">

## Autofilled Venmo Request
<img src="https://github.com/pomkos/payme/blob/main/images/venmo.png" width="620">

## Default View with Inputs
<img src="https://github.com/pomkos/payme/blob/main/images/yes_input.png" width="620">

## Default View without Inputs
<img src="https://github.com/pomkos/payme/blob/main/images/no_input.png" width="620">

## Expanded Page
<img src="https://github.com/pomkos/payme/blob/main/images/whole_page.png" width="620">

## Postgres Database outline
<img src="https://peti.drawerd.com/projects/1462/render_svg?mode=accurate&share_key=b3ecaddcca136ca0dee2d537f06e22" width="720">

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
5. Access the portfolio at `localhost:8501`

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

nohup streamlit run payme.py "postgres_user:postgres_pw" "postgres_ip" "postgres_port" --server.port 8503 &
```

3. Edit crontab so portfolio is started when server reboots

```
crontab -e
```

4. Add the following to the end, then save and exit

```
@reboot /home/payme.sh "postgres_user:postgres_pw" "postgres_ip" "postgres_port" --server.port 8503
```

5. Access the website at `localhost:8503`
