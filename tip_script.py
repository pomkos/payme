import streamlit as st
import numpy as np
import pandas as pd
st.title('Venmo Requests Calculator')

def venmo_requester(my_dic, total, tax=0, tip=0, misc_fees=0):
    """
    Returns lump sums to request using venmo
    
    input
    -----
    my_dic: dict
        Dictionary of name:[list of prices]
    total: float
        Total shown on receipt, charged to your card
    tax: float
        Tax applied in dollars, not percent
    tip: float
        Amount tipped in dollars, not percent
    misc_fees: float
        Sum of all other fees not accounted for, like delivery fee, etc
        
    output
    -----
    request: dict
        Dictionary of name:amount, indicating how much to charge each person
    """
    precheck_sum = 0
    for key in my_dic.keys():
        precheck_sum += sum(my_dic[key])
    
    precheck_sum = round(precheck_sum+tax+tip+misc_fees,2)
    if total != precheck_sum:
        return st.write(f"You provided {total} as the total, but I calculated {precheck_sum}")
    else:
        num_ppl = len(my_dic.keys())
        tip_perc = tip/total
        tax_perc = tax/total
        fee_part = misc_fees/num_ppl
        request = {}
        rounded_sum = 0
        for key in my_dic.keys():        
            my_list = my_dic[key]

            my_total = sum(my_list)
            tax_part = tax_perc * my_total
            tip_part = tip_perc * my_total

            person_total = round(my_total + tax_part + fee_part + tip_part,2)
            rounded_sum += person_total
            request[key] = person_total
    
        if rounded_sum < total:
            rounding_error = round((total - rounded_sum)/num_ppl,2)
            for key in request.keys():
                request[key] += rounding_error
            
            new_total = 0
            for key in request.keys():
                new_total += request[key]
            with st.beta_expander(label='What just happened?'):
                st.write(f"""
                1. After rounding the calculated sum was ${round(rounded_sum,2)}, but the total charged to your credit card was ${round(total,2)}
                    * Rounding error found and adjusted for by adding ${round(rounding_error,2)} to each person.
                2. ${round(new_total,2)} has been accounted for""")
        elif rounded_sum > total:
            return st.write(f"Uh oh! My calculated venmo charge sum is ${rounded_sum} but the receipt total was ${round(total,2)}")
        else:
            st.write(f"The venmo charge sum is same as the receipt total, no rounding correction needed")
        st.write(
            '''## Output
### Venmo Requests: 
How much to charge each person
            ''')
        output_money = {}
        for key in request.keys():
            output_money[key] = round(request[key],2)
        output_money
        st.write(
            '''### Venmo Comments: 
Copy and paste these into the venmo app
            ''')
        output_comment = {}
        for key in request.keys():
            output_comment[key] = f'Food was ${round(sum(my_dic[key]),2)}, tip was {round(tip_perc*100,2)}%, tax was {round(tax_perc*100,2)}%, fees were ${round(fee_part,2)}'
        output_comment

st.write('## User input')

demo_receipt = '''Russell: 29, 10, 1
Peter: 10,20.23, 1'''

receipt_input = st.text_area(label="Add name and food prices",value=demo_receipt)

col1, col2, col3 = st.beta_columns(3)

with col1:
    fees_input = st.number_input("Fees in dollars", 2.89)
with col2:
    tax_input = st.number_input("Tax in dollars", 10.23)
with col3:
    tip_input = st.number_input("Tip in dollars", 20)

total_input = st.number_input("Total with Tip",104.35)

# Receipt formatting
splitted = receipt_input.split('\n')
data = {}
for line in splitted:
    # get each line by itself, separate name from values
    alone = line.split(':')
    name = alone[0].replace(' ','')
    
    # create a list of numbers from string
    alone[1] = alone[1].replace(' ','')
    nums = alone[1].split(',')
    new_list = [float(x) for x in nums]
    
    # data in dictionary
    data[name] = new_list

venmo_requester(my_dic = data, total=total_input, tax=tax_input, tip=tip_input, misc_fees=fees_input)

# Fun stuff
button = st.button(label='Awesome job!')
if button == True:
    st.balloons()
