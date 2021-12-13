#!/bin/bash
source $HOME/miniconda3/bin/activate

echo "What would you like to do?"
echo "[1] Install payme"
echo "[2] Add to crontab"
echo
read input

function edit_cron(){
    crontab -l > file
    echo "# start after each reboot" >> file
    echo "@reboot      $HOME/projects/payme/start_me.sh" >> file
    crontab file
    rm file
    echo "payme will start every reboot"
}

function install_payme()
{
    conda create -y --name "payme_env"
    conda activate payme_env
    conda install -y -c conda-forge python=3.8
    cd $HOME/projects/payme
    pip install --no-input -r requirements.txt
    nohup streamlit run payme.py --server.port 8501 &
    conda deactivate

    read cron "Append payme to crontab? [y/n] "
    echo


    if [[ $cron == "Y" || $cron == "y" ]]
    then
        edit_cron
    fi

    echo "payme installed on port 8501"

}

if [[ $input == 1 ]]
then
    install_payme
elif [[ $input == 2 ]]
then
    edit_cron
else
    echo "No option selected"
    exit 1
fi
