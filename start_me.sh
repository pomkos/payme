#!/bin/bash
# For use with crontab
source ~/miniconda3/bin/activate

cd $HOME/projects/payme
conda activate payme_env # activate the new conda env
nohup streamlit run payme.py --server.port 8501 & # run in background

echo "Running payme.py on port 8501!"
