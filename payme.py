# core app. Redirects to appropriate apps.

# libraries
import streamlit as st
st.set_page_config(page_title = 'Venmo Calculator')
import pandas as pd
import numpy as np
import re
import sys

# files
from apps import calculator as calc
from apps import manual_mode as mm

# arguments
us_pw = sys.argv[1]  # user input: "my_user:password"
db_ip = sys.argv[2]  # user input: 192.168.1.11
port = sys.argv[3]   # user input: 5432
db_info = [us_pw, db_ip, port]

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
<script src="https://cdn.jsdelivr.net/npm/darkmode-js@1.5.7/lib/darkmode-js.min.js"></script>
<script>
  function addDarkmodeWidget() {
    new Darkmode().showWidget();
  }
  window.addEventListener('load', addDarkmodeWidget);
</script>

"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def start(button=None):
    '''
    Main app. Creates the GUI and redirects requests to the appropriate scripts. The Thalamus.
    '''
#     if st.experimental_get_query_params():
#         params = use_params()
#         st.write(params)
#         if params[-1] == True: # if the link is shared
#             st.info("Looks like this is a shared link, so we filled in the info for you!")
#             select_input = params[-2]
    params = None
    if type(button) == str:
        pass
    select_input = st.sidebar.radio("Select input type", options=['Manual','Auto (alpha)','Image (beta)'],index=0)
    if 'beta' in select_input:
        from apps import beta_image_rec as ir
        gui = '(Beta)'
        receipt_input ,fees_input, tax_input, tip_input = ir.auto_input(gui)
    elif 'alpha' in select_input:
        gui = '(Alpha)'
        receipt_input, fees_input, tax_input, tip_input = mm.manual_input(gui, params)
    else:
        gui = ''
        receipt_input, fees_input, tax_input, tip_input = mm.manual_input(gui, params)
            
    total_input, data = calc.total_calculator(receipt_input, fees_input, tax_input, tip_input)
        
    try:
        # gets a dictionary of total spent, dictionary of spent on food, percent tip, percent tax, and misc fees per person
        if "alpha" in select_input:
            request_money, tip_perc, tax_perc, fee_part, messages = calc.venmo_calc(my_dic = data, total=total_input, tax=tax_input, tip=tip_input, misc_fees=fees_input, clean=True)
        else:
            # if manual, then show the html table
            request_money, tip_perc, tax_perc, fee_part, messages = calc.venmo_calc(my_dic = data, total=total_input, tax=tax_input, tip=tip_input, misc_fees=fees_input, clean=False)
            mm.html_table(messages, request_money)
    except ZeroDivisionError:
        request_money = None
   
    if not request_money:
        st.info("See the how to for more information!")
        st.stop()
        
    # add parameters to url for easy sharing
    if st.button("Share the calculation"):
        from apps import alpha_clipboard as ac:
            ac.set_params(my_dic = data, total=total_input, tax=tax_input, tip=tip_input, misc_fees=fees_input,view=select_input ,share=True,)
        
    ###################
    # TESTING GROUNDS #
    ###################
    if ('alpha' in select_input) and request_money:
        from apps import alpha_users
        alpha_users.app(my_dic = request_money, total=total_input, 
                        tax=tax_input, tip=tip_input, misc_fees=fees_input,
                        messages = messages, db_info = db_info)
        "_________________________"

def app():
    '''
    Only purpose is to start the app from bash script. Own function so the rest of the functions can be organized in a logical way.
    '''
    start(button='start')

app()