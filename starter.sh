#!/bin/bash

db_user="postgres:helllo" # Database  login in the format of "user:pw". Quotes included
db_ip=192.168.1.240   # Database local ip such as 192.168.1.11, without http. Quotes not included
db_port=5432 # Database port such as 5432. Quotes not included

streamlit run payme.py $db_user $db_ip $db_port --server.port 8502