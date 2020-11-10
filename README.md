# money_requesting
Just a simple repo to calculate how much to request from people after a night out

# How-To

1. Clone this repo
2. Create a new conda environment with python 3.6, then `pip install -r recommendations.txt`
3. Save this script somewhere, make sure to make executable with `chmod +x my_script.sh`
```
#!/bin/bash

source ~/anaconda3/etc/profile.d/conda.sh

cd /dir/to/cloned_repo
conda activate my_env # activate the new conda env

nohup streamlit run tip_script.py & # run in background
```

You can exit the terminal and streamlit will continue serving the python file. 

# Screenshot

NOTE: The `Submit to Database` button is there for funsies only. Saving to database is not yet implemented.

## Homepage
![](initial_page.png?raw=true)

## Sample Input
![](sample_input.png?raw=true)

## Sample Output
![](sample_output.png?raw=true)
