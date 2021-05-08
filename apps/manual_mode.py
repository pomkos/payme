# Web GUI for manual input option

import streamlit as st
import pandas as pd

def name_input():
    '''
    Ask for and format names
    '''
    import re
    my_names = ''
    names = st.text_input("Add names below:")
    if names:
        names_list = re.findall(r'\w+', names)
        for x in names_list:
            my_names += x
            my_names += ','
        return my_names.strip(',')
    
def name_finder(receipt):
    '''
    First attempt at automatically finding the names of people in receipts
    '''
    from apps import db_tool as db
    import re
    all_names = db.name_loader()
    receipt = receipt.replace(',', ' ').lower()
    words = re.findall(r'\w+', receipt)
    st.write("--------------------")
    my_names = ''
    for row in words:
        for name in all_names['names']:
            if name == row:
                my_names += f"{name},"
                st.success(f"Detected {name.title()}")
    if my_names != '':
        my_names = my_names.strip(',') # get rid of last comma
        feedback = st.checkbox("These are the right names",value=True)
        if feedback:
            return my_names
        else:
            return name_input()
    else:
        st.warning("Sorry, the names were not found.")
        return name_input()


def find_reg_num(my_string, num_type):
    '''
    Helper function to find floats within a string using regex
    
    my_str: str
        String that contains number
    num_type: str
        One of `tax`, `tip`, or `fees`, indicating which number to return
    '''
    import re
    regex_code = '(\d+?\.\d+)'
    result = float(re.findall(f"%%{num_type}: {regex_code}", my_string)[0])
    return result


def manual_mode():
    '''
    Completely manual input
    '''
    st.title("Venmo Requests Calculator: Manual Mode")
    st.write("Give us some info, we'll give you venmo request links!")
    with st.beta_expander(label='How To'):
        st.write(f"""
            1. Input the name and itemized money spent in a format of:
                ```
                Peter: 20.21,5.23, 3.21
                Russell: 11.01, 15.89, 1.99
                ```
                Or on a single line:
                ```
                Peter 20.21 5.23 3.21 Russell 11.01 15.89 1.99
                ```
                Or with a split cost (Peter and Russell pay 8 each)
                ```
                Peter and Russell 16
                Peter: 20.21, 5.23
                Russell 11.01 15.89 1.99
                ```
            2. Input the rest of the fees or tips as needed""")
    description = st.text_input(label="(Optional) Description, like the restaurant name")
    receipt_input = st.text_area(label="Add name and food prices*", height=150)
    
    if '---DO NOT DELETE BELOW---:' in receipt_input:

        # then the meals were claimed. This section is here to avoid
        # user having to put in tax/tip/fees twice
        import re
        tax_val = find_reg_num(receipt_input, 'tax')
        tip_val = find_reg_num(receipt_input, 'tip')
        fees_val = find_reg_num(receipt_input, 'fees')
        
        # Use regex to find location of added info, then remove it
        # otherwise tax/tip/fees will show up as people in
        # venmo request table
        result = re.search("---DO NOT DELETE BELOW---:", receipt_input)
        loc = [int(x) for x in result.span()]
        receipt_input = receipt_input[:loc[0]]
    else:
        tax_val = 0.0
        tip_val = 0.0
        fees_val = 0.0
    col1, col2 = st.beta_columns(2)
    col3, col4 = st.beta_columns(2)

    with col1:
        fees_input = st.number_input("Fees in dollars",step=1.0,value=fees_val)
    with col2:
        tax_input = st.number_input("Tax in dollars",step=1.0,value=tax_val)
    with col3:
        tip_input = st.number_input("Tip in dollars",step=5.0, value=tip_val)
    with col4:
        discount = st.number_input("Discount in dollars",step=1.0)
        discount = discount*-1
    return_me = {'description':description, 
                 'receipt_input':receipt_input, 
                 'fees_input':fees_input, 
                 'tax_input':tax_input,
                 'tip_input':tip_input,
                 'discount':discount,
                 'contribution':0.0} # tip to establishment. Only for ubereats
    return return_me