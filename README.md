# Table of Contents

1. [Description](#payme)
2. [Screenshots](#screenshots)
    1. [Autofilled Venmo Request](#autofilled-venmo-request)
    2. [Default View with Inputs](#default-view-with-inputs)
    3. [Default View without Inputs](#default-view-without-inputs)
    4. [Expanded Page](#expanded-page)
3. [How-Tos](#how-tos)
    1. [Run](#run)
    2. [Host](#host)
    3. [Catch-all Script](#catch-all-script)

# PayMe
Just a simple repo to calculate how much to request from people after a night out

# Screenshots

## Autofilled Venmo Request
<img src="https://github.com/pomkos/payme/blob/main/images/venmo.png" width="620">

## Default View with Inputs
<img src="https://github.com/pomkos/payme/blob/main/images/yes_input.png" width="620">

## Default View without Inputs
<img src="https://github.com/pomkos/payme/blob/main/images/no_input.png" width="620">

## Expanded Page
<img src="https://github.com/pomkos/payme/blob/main/images/whole_page.png" width="620">

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

nohup streamlit run payme.py --server.port 8503 &
```

3. Edit crontab so portfolio is started when server reboots

```
crontab -e
```

4. Add the following to the end, then save and exit

```
@reboot /home/payme.sh
```

5. Access the website at `localhost:8503`

## Catch-All Script

The following is just a simple script to help run various streamlit programs in the background. 

### To run: 

`./script_name.sh -f folder_name -e env_name -p port_num`

### Script:
```
################################################################################
# Help                                                                         #
################################################################################
Help()
{
   # Display Help
   echo
   echo "Starts a streamlit python script."
   echo
   echo "Syntax: scriptTemplate [-h|f|e|p]"
   echo "options:"
   echo "f     Folder python script is in."
   echo "e     Conda environment to use."
   echo "p     Port to publish on."
   echo "h     Print this Help."
   echo
}

################################################################################
# Main program                                                                 #
################################################################################
run_script()
{
    source ~/anaconda3/etc/profile.d/conda.sh

    cd ~/projects/$folder
    conda activate $my_env # activate the new conda env
    nohup streamlit run $folder.py --server.port $port & # run in background

    echo "Running $folder.py on port $port using PID $!"
}


# get options
while getopts ":h:f:e:p:" option; do
    case $option in
        h)  #display help
            Help
            exit;;
        \?) #incorrect option
            echo "Error: Invalid option"
            exit;;
        f) folder=${OPTARG};;
        e) my_env=${OPTARG};;
        p) port=${OPTARG};;
    esac
done

run_script
```
