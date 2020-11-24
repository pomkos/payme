import streamlit as st
st.title('Venmo Requests Calculator')

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

class saveInfo():
    def __init__(self, my_total, my_food, tip_perc, tax_perc, fee_part):
        '''
        Initialize the sqlite database
        
        input
        -----
        my_total: dict
            Dictionary of name:float, representing the total requested from each individual
        my_food: dict
            Dictionary of name:float, representing the total spent on food by each individual
        tip_perc: float
            Percent (in decimal form) the whole group tipped
        tax_perc: float
            Percent (in decimal form) the whole group spent on tax
        fee_part: float
            Misc fees evenly divided amongst all individuals
        '''
        import sqlalchemy as sq
        import datetime as dt
        from pytz import timezone 

        # initialize engine
        engine = sq.create_engine('sqlite:///payme.db')
        meta = sq.MetaData()
        
        # table format in db
        self.payme_now = sq.Table(
           'payme_now', meta, 
           sq.Column('id', sq.Integer, primary_key = True), 
           sq.Column('date',sq.DateTime),
           sq.Column('name', sq.String), 
           sq.Column('food', sq.Float),
           sq.Column('tip',sq.Float),
           sq.Column('tax',sq.Float),
           sq.Column('fees',sq.Float),
           sq.Column('total',sq.Float)
        )
        
        # format data into proper list of dictionaries
        tz = timezone('US/Eastern')
        result = []
        
        for key in my_total.keys():
            person = {
                'date':dt.datetime.now(tz),
                'name':key,
                'food':my_food[key],
                'tip':round(my_food[key] * tip_perc,2),
                'tax':round(my_food[key] * tax_perc,2),
                'fees':fee_part,
                'total':my_total[key][0] # its a dictionary of lists, with each list having only the total
            }
            
            result.append(person)
        
        meta.create_all(engine) # not sure why its needed, but its in the tutorial so ... :shrug:
        self.engine = engine
        self.result = result
        
    def save_table(self):
        '''
        Saves information to database
        '''
        import datetime as dt
        
        conn = self.engine.connect()
        result = conn.execute(self.payme_now.insert(), self.result)
        
    def read_table(self):
        '''
        Returns the entire database
        '''
        import pandas as pd
        
        return pd.read_sql_table('payme_now',self.engine,parse_dates='date')


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
   
    precheck_sum = round(sum(my_dic.values())+tax+tip+misc_fees,2)
    total = round(total,2) # otherwise get weird 23.00000005 raw totals
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
            my_total = my_dic[key]

            tax_part = tax_perc * my_total
            tip_part = tip_perc * my_total

            person_total = my_total + tax_part + fee_part + tip_part
            rounded_sum += person_total
            request[key] = person_total
        # rounded_sum = round(rounded_sum,2)
        if (rounded_sum < total+0.1) | (rounded_sum > total-0.1):
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
            output_comment[key] = f'Food was ${round(my_dic[key],2)}, tip was {round(tip_perc*100,2)}%, tax was {round(tax_perc*100,2)}%, fees were ${round(fee_part,2)}'
        output_comment
        
        return output_money, my_dic, tip_perc, tax_perc, fee_part

st.write('## User input')
## Demo
with st.beta_expander(label='How To'):
    st.write(f"""
        1. Input the name and itemized money spent in a format of:
            ```
            Peter: 20.21,5.23, 3.21
            Russell: 101.01, 15.89, 1.99
            ```
            Or on a single line:
            ```
            Peter 20.21 5.23 3.21 Russell 101.01 15.89 1.99
            ```
            Or with a split cost (Peter and Russell pay 8 each)
            ```
            Peter and Russell 16
            Peter: 20.21, 5.23
            Russell 101.01 15.89 1.99
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

import re
pattern = '((?:[A-Za-z ,:])+)((?:[\\d.]+[, ]*)+)'
# (                name group with optional space, colon, and comma
#   (?:               
#     [A-Za-z ,:]  capture all alpha which includes "and"
#   )+             one or more times
# )  
# (                number group mathching numbers separated by comma or space
#   (?:         
#     [\\d.]+[, ]* (sorry eruopeans)
#   )+
# )

# split string on the delimiters: 'and' '<space>' ':' ','
def parse_alpha(alpha):
    return list(filter(None, re.split('(?:and| |:|,)+', alpha)))

# split "12.2 12.3 56 53.2" -> "[12.2,12.3,56,53.2]"
def parse_numbers(numbers):
    return list(filter(None, re.split('(?:[^\\d\\.])', numbers)))

# a dictionary of name(s) and sum of amount
raw_pairs = [
    (
        parse_alpha(alpha),
        sum([float(i) for i in parse_numbers(numbers)])
    ) for (alpha, numbers) in re.findall(pattern, receipt_input)
]

# combine all split costs with the people involved
data = {}
for (people, amount) in raw_pairs:
    for person in people:
        if not person in data:
            data[person] = round(amount/len(people),2)
        else:
            data[person] += round(amount/len(people),2)

precheck_sum = sum(data.values())
total_input = st.number_input("Calculated Total",step=1.0,value=round(precheck_sum+tax_input+tip_input+fees_input,2))

try:
    # gets a dictionary of total spent, dictionary of spent on food, percent tip, percent tax, and misc fees per person
    data
    total_input
    my_total, my_food, tip_perc, tax_perc, fee_part = venmo_requester(my_dic = data, total=total_input, tax=tax_input, tip=tip_input, misc_fees=fees_input)
except Exception as e:
    e # print exception in the browser
    
##### LIVE TESTING AREA #####

#############################
    
# Fun stuff
button_save = st.button(label='Submit to Database')
button_show = st.button(label='Show the Database')

if button_save == True:
    saveus = saveInfo(my_total, my_food, tip_perc, tax_perc, fee_part)
    saveus.save_table()
    st.balloons()
    
if button_show == True:
    showus = saveInfo(my_total, my_food, tip_perc, tax_perc, fee_part)
    dataframe = showus.read_table()
    dataframe
