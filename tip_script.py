import streamlit as st
st.title('Venmo Requests Calculator')

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>

"""
# st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def db_save_table(dataframe, name, db = 'money_split.db', folder='sqlite:///C:\\Users\\albei\\OneDrive\\Desktop\\streamlit_test\\', if_exists='fail', index=False):
    '''
    Saves dataframe to bike_data.db by default
    
    input
    -----
    dataframe: df
        Dataframe to save to sql
    name: str
        Name to save dataframe as
    db: str
        Name of database
    folder: str
        Location of database. Must end in backslash
    if_exists: string
        'fail' or 'replace', what to do if table name exists in db
    index: bool
        False if index should be dropped
        True if index should be saved as new column
    '''
    import sqlalchemy as sq
    from datetime import datetime
    from pytz import timezone
    tz = timezone('US/Eastern')
    now = datetime.now(tz) 

    dt_string = now.strftime("%m-%d-%Y %H:%M:%S")

    location = folder + db
    cnx = sq.create_engine(location)
    dataframe.to_sql(name, con=cnx, if_exists=if_exists, index=index)
    return f'Dataframe saved to {location} as {name} on {dt_string}'

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
    import pandas as pd
    precheck_sum = 0
    for key in my_dic.keys():
        precheck_sum += sum(my_dic[key])
    
    precheck_sum = round(precheck_sum+tax+tip+misc_fees,2)
    if total != precheck_sum:
        return st.write(f"You provided {total} as the total, but I calculated {precheck_sum}")
    else:
        num_ppl = len(my_dic.keys())
        tax_perc = tax/(total-tip-misc_fees-tax)
        tip_perc = tip/(total-tax-misc_fees-tip)
        fee_part = round(misc_fees/num_ppl,2)
        request = {}
        rounded_sum = 0
        for key in my_dic.keys():        
            my_list = my_dic[key]

            my_total = sum(my_list)
            tax_part = tax_perc * my_total
            tip_part = tip_perc * my_total

            person_total = my_total + tax_part + fee_part + tip_part
            rounded_sum += person_total
            request[key] = person_total
        rounded_sum = round(rounded_sum,2)
        if rounded_sum < total:
            rounding_error = round((total - rounded_sum)/num_ppl,2)
            for key in request.keys():
                request[key] += rounding_error
            
            new_total = 0
            for key in request.keys():
                new_total += request[key]
            with st.beta_expander(label='What just happened?'):
                st.write(f"""
                1. After rounding the calculated sum was ${rounded_sum}, but the total charged to your credit card was ${round(total,2)}
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
            output_money[key] = [round(request[key],2)]
        df_out = pd.DataFrame.from_dict(output_money)
        df_out = df_out.reset_index(drop=True)
        df_out
        
        st.write(
            '''### Venmo Comments: 
Copy and paste these into the venmo app
            ''')
        output_comment = {}
        for key in request.keys():
            output_comment[key] = f'Food was ${round(sum(my_dic[key]),2)}, tip was {round(tip_perc*100,2)}%, tax was {round(tax_perc*100,2)}%, fees were ${round(fee_part,2)}'

st.write('## User input')
## Demo
with st.beta_expander(label='How To'):
    st.write(f"""
    1. Input the name and itemized money spent in the format of:
        ```
        Peter: 20.21,5.23, 3.21
        Russell: 101.01, 15.89, 1.99
        ```
    2. Input the rest of the fees or tips as needed""")
   
receipt_input = st.text_area(label="Add name and food prices")
            
col1, col2, col3 = st.beta_columns(3)

with col1:
    fees_input = st.number_input("Fees in dollars",step=1.0)
with col2:
    tax_input = st.number_input("Tax in dollars",step=1.0)
with col3:
    tip_input = st.number_input("Tip in dollars",step=1.0)

# Receipt formatting
splitted = receipt_input.split('\n')
data = {}
for line in splitted:
    try:
        # get each line by itself, separate name from values
        alone = line.split(':')
        name = alone[0].replace(' ','')

        # create a list of numbers from string
        alone[1] = alone[1].replace(' ','')
        nums = alone[1].split(',')
        new_list = [float(x) for x in nums]

        # data in dictionary
        data[name] = new_list
    except:
        ''
precheck_sum = 0
for key in data.keys():
    precheck_sum += sum(data[key])
    
total_input = st.number_input("Calculated Total",step=1.0,value=precheck_sum+tax_input+tip_input+fees_input)

try:
    venmo_requester(my_dic = data, total=total_input, tax=tax_input, tip=tip_input, misc_fees=fees_input)
except:
    ''
# Fun stuff
button = st.button(label='Submit to Database')
if button == True:
    st.balloons()
