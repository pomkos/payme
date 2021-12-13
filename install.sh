#!/bin/bash
source $HOME/miniconda3/bin/activate

echo "What would you like to do?"
echo "[1] Install payme"
echo "[2] Edit crontab"
echo
read input

function edit_cron(){
    crontab -l > file
    echo "nohup streamlit run $HOME/projects/payme/payme.py --server.port 8501 &" >> file
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
fi
