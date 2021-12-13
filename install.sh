#!/bin/bash
source $HOME/miniconda3/bin/activate

conda create -y --name "payme_env"
conda activate payme_env
conda install -y -c conda-forge python=3.8
cd $HOME/projects/payme
pip install --no-input -r requirements.txt
nohup streamlit run payme.py --server.port 8501 &
conda deactivate

echo "payme installed on port 8501"
