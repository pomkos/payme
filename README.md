[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/pomkos/payme/main/payme.py)

# Table of Contents

1. [Description](#payme)
2. [Screenshots](#screenshots)
    1. [Delivery App Mode](#delivery-app-mode-default)
    2. [Manual Mode](#manual-mode)
    3. [What Happened](#what-happened)
    4. [Output](#output)
    5. [Venmo Preview](#venmo-preview)
3. [How-Tos](#how-tos)
    1. [Run](#run)
    2. [Host](#host)
4. [Outline](#outline)
    1. [Code Structure](#code)
    2. [Databases](#databases)

# PayMe
Just a simple repo to calculate how much to request from people after a night out

# Screenshots

## Delivery App Mode (default)

 <img src="https://github.com/pomkos/payme/blob/main/images/default_view.png" width="620"> 

## Manual Mode

<img src="https://github.com/pomkos/payme/blob/main/images/manual_mode.png" width="620">

## What Happened

<img src="https://github.com/pomkos/payme/blob/main/images/what_happened.png" width="620">

## Output

<img src="https://github.com/pomkos/payme/blob/main/images/testaurant_output.png" width="620">

## Venmo Preview

<img src="https://github.com/pomkos/payme/blob/main/images/venmo_preview.png" width="310">

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

```bash
sudo chmod +x install.sh
sudo chmod +x start_me.sh

./install.sh
```

Installer script will:

1. Create new environment
2. Install all required python libraries
3. Add a cronjob to cron (if user desires, can be done post installation as well)
4. Start the payme script on `port 8501`

# Outline

## Code

The codebase is organized as such:

```
payme
  |-- apps
      |-- calculator.py     # called by all scripts for the actual calculations
      |-- db_tool.py        # includes helper class to connect to sqlite db and extract currency info
      |-- doordash.py       # specific to doordash receipts, extracts all info
      |-- food_select.py    # used by the complex receipt receiver and the claim your meal pages
      |-- manual_mode.py    # used by default view of payme, using user provided info
      |-- ubereats.py       # specific to ubereats receipts, extracts all info
  |-- data
      |-- currency.db       # stores currency, country, rate info
      |-- food.db           # stores complex receipt info so users can select foods
      |-- names.db          # stores names, variations of names, and mispellings to automatically parse these from all inputs
  |-- images
  |-- .gitignore
  |-- README.md
  |-- payme.py              # the brains behind it all, redirects user provided information to the appropriate scripts in apps folder
  |-- requirements.txt
```

## Databases

### Food.db

#### receipt table

Stores information from the complex receipt receiver on payme

| item                            | price | amount | name                 | people                                | date       |
| ------------------------------- | ----- | ------ | -------------------- | ------------------------------------- | ---------- |
| Buck to the Future (1.0 bought) | 14.0  | 1.0    | Roosevelt Room_05-21 | Peter, Matt, Steve, Julie, Aron, Kyle | 2021-05-21 | 

#### food table

Stores information from the claim your meal section on payme. This is what is shown when users click "see everyone's claimed meals"

| name  | food                                | price | amount | total_item_price | label              |
| ----- | ----------------------------------- | ----- | ------ | ---------------- | ------------------ |
| Peter | [dessert] medovik cake (1.0 bought) | 8.00  | 1.0    | 8.00             | Russia House_05-02 | 

### Currency.db

#### country_currency table

| country        | currency       | code |
| -------------- | -------------- | ---- |
| United Kingdom | Pound Sterling | GBP  | 


#### currency_rates table

| rate     | country        | currency       | code | date_updated |
| -------- | -------------- | -------------- | ---- | ------------ |
| 0.729266 | United Kingdom | Pound Sterling | GBP  | 2021-03-25   | 
### Names.db

#### names table

Just a database of names with different spellings, for easier parsing of info

| names  |     |
| ------ | --- |
| bl@ise |     |
