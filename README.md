# PayMe
Just a simple repo to calculate how much to request from people after a night out

# How-To

1. Clone this repo `git clone https://github.com/pomkos/money_requesting`
2. Create a new conda environment with python 3.6, then install the libraries
  ```bash
  conda create --name tip_env python=3.6
  conda activate tip_env
  cd money_requesting
  pip install -r recommendations.txt
  ```
3. Run within the environment with `streamlit run tip_env`, it will be accessible at localhost:8501

To run in "prod":

* Create the following script
```
#!/bin/bash

source ~/anaconda3/etc/profile.d/conda.sh

cd /dir/to/tip_env
conda activate tip_env # activate the new conda env

nohup streamlit run tip_script.py & # run in background
```
* Make it executable with `chmod +x my_script.sh`
* You can exit the terminal and streamlit will continue serving the python file. 
* Cronjob to have the server start at each reboot:
```bash
crontab -e
@reboot /home/peter/scripts/payme.sh #add this line at the bottom
```

# Screenshots

## Default View without Inputs
![](images/no_input.png?raw=true)

## Default View with Inputs
![](images/yes_input.png?raw=true)

## Expanded Page
![](images/whole_page.png?raw=true)

