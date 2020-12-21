import streamlit as st
import re
import sys

us_pw = sys.argv[1]  # user input: "my_user:password"
db_ip = sys.argv[2]  # user input: 192.168.1.11
port = sys.argv[3]   # user input: 5432

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

class receiptFormat():
    # Receipt formatting
    def __init__(self):
        '''
        Formats string input of name/money using the following regix pattern.
        
        (                name group with optional space, colon, and comma
          (?:               
            [A-Za-z ,:]  capture all alpha which includes "and"
          )+             one or more times
        )  
        (                number group matching numbers separated by comma or space
          (?:         
            [\\d.]+[, ]* (sorry eruopeans)
          )+
        )
        '''
        self.pattern = '((?:[A-Za-z ,:])+)((?:[\\d.]+[, ]*)+)'

    def parse_alpha(self,alpha):
        'Splits string on delimiter including "and" "<space>" ":" ","'
        return list(filter(None, re.split('(?:and| |:|,)+', alpha)))

    def parse_numbers(self,numbers):
        'Splits "12.2 12.3 56 53.2" -> "[12.2,12.3,56,53.2]"'
        return list(filter(None, re.split('(?:[^\\d\\.])', numbers)))
    
class saveInfo():
    def __init__(self, my_total=0, my_food=0, tip_perc=0, tax_perc=0, fee_part=0,showme='yes'):
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
        import os
        import datetime as dt
        from pytz import timezone 

        # initialize engine
        engine = sq.create_engine(f'postgres://{us_pw}@{db_ip}:{port}')
       
        meta = sq.MetaData()
        if showme=='no':
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
            self.result = result
        meta.create_all(engine) # not sure why its needed, but its in the tutorial so ... :shrug:
        self.engine = engine

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
    
def manual_input():
    '''
    Cut from app() function to make way for screenshot. 
    Manual input of costs, fees, tax, tips.
    '''
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

    receipt_input = st.text_area(label="Add name and food prices*")
    col1, col2, col3 = st.beta_columns(3)

    with col1:
        fees_input = st.number_input("Fees in dollars",step=1.0)
    with col2:
        tax_input = st.number_input("Tax in dollars",step=1.0)
    with col3:
        tip_input = st.number_input("Tip in dollars",step=5.0)
    return receipt_input ,fees_input, tax_input, tip_input

@st.cache
def ocr_image(my_receipt='pdf'):
    '''
    Use OCR to extract information from an image. When DoorDash groups is used.
    '''
    import pytesseract as tes
    from PIL import Image
    import pandas as pd
    # process the image
    if my_receipt == 'pdf':
        text_str = str(((tes.image_to_string(Image.open(f'temp/page.jpg')))))
    else:
        text_str = tes.image_to_string(Image.open(my_receipt))
    text_str = text_str.lower().split("\n")
    text_str = pd.Series(text_str)

    # get rid of empty rows
    text_str = text_str.replace('',float('NaN'))
    text_str = text_str.dropna().reset_index(drop=True)
    
    return text_str

@st.cache
def ocr_pdf(my_receipt):
    '''
    Use OCR to extract information from an image. When DoorDash groups is used.
    '''
    from pdf2image import convert_from_bytes
    
    # process the image
    pages = convert_from_bytes(my_receipt.read())
    pages[0].save(f"temp/page.jpg",'JPEG')
    
def auto_input(input_type):
    '''
    Main auto function, decide pdf vs image then organize extracted info
    
    input
    -----
    input_type: str
        Either pdf or image. Defines what type of file is uploaded.
    '''
    from PIL import Image
    if input_type == 'image':
        my_receipt = st.file_uploader("Upload a screenshot",type=['png','jpg','jpeg'])
        if not my_receipt:
            st.info("Upload a screenshot of the receipt!")
            st.stop()
        text_str = ocr_image(my_receipt=my_receipt)
    else:
        my_receipt = st.file_uploader("Upload a receipt",type=['pdf'])
        if not my_receipt:
            st.info("Upload receipt in PDF format!")
            st.stop()
        ocr_pdf(my_receipt)
        text_str = ocr_image(my_receipt='pdf')
    with st.beta_expander(label="OCR feedback"):
        col_img, col_extract = st.beta_columns(2)
        with col_img:
            st.success("Uploaded!")
            try:
                st.image(Image.open(my_receipt),width=250)
            except:
                st.warning("Bug with showing image")
    extracted = {} # dictionary of all extracted info
    ###
    # Extract all prices
    ###
    monies = text_str[text_str.str.contains("\$")]
    try:
        monies = monies.str.replace('$','').astype(float)
    except:
        st.info("Currently only supporting DoorDash group orders. Try manual input!")
        st.stop()
    extracted['monies'] = monies.reset_index(drop=True)
    
    ### 
    # Extract people
    ###    
    # number of people
    parts = text_str[text_str.str.contains('participants')]
    extracted['participants'] = int(list(parts.str.extract("(\d\d?) participants")[0])[0])
    extracted['items'] = int(list(parts.str.extract("(\d\d?) items")[0])[0])
    
    my_names = st.text_area("Separate names with a comma: peter, Russell")
    if not my_names:
        st.info(f"""Add all __{extracted['participants']} names__ in the order that they appear on the receipt.""")
        st.stop()
    my_names = my_names.split(',')
    if len(my_names)!=extracted['participants']:
        # if user didn't provide the right number of names, script won't work
        st.warning(f"I detected __{extracted['participants']}__ people on this receipt, but you provided __{len(my_names)}__")
        st.stop()
    
    # format input to remove space and make it all lowercase
    names = [n.lower().strip() for n in my_names]
    names.append('subtotal')
    names = tuple(names)
    names_dict = {} # dictionary of names and their iloc in the series
    for i, s in text_str.iteritems():
        for name in names:
            if s.startswith(name):
                names_dict[name] = i
    # number of items per person
    for i in range(len(names)):
        # find how many food items each person ate
        try:
            start = names_dict[names[i]]
            end = names_dict[names[i+1]]
            extracted[names[i]] = len(text_str[start+1:end])
        except:
            pass

    ###
    # Extract costs per person
    ###
    all_money = extracted['monies'] # each item is on its own line
    people_money = all_money.loc[:extracted['items']-1] # the first X rows are all items, subtract one cuz ending is inclusive
    my_receipt = {}
    try:
        for name in names[:len(names)-1]: # the last one is always subtotal
            my_receipt[name] = people_money.loc[:extracted[name]-1]
            for i in range(extracted[name]):
                try:
                    people_money = people_money.drop(i)
                except:
                    pass
            people_money = people_money.reset_index(drop=True)
    except:
        st.warning("Are you sure the names were provided in the right order?")
    receipt_input = ''
    for name in my_receipt.keys():
        receipt_input += f'{name}: {list(my_receipt[name])} '
    receipt_input = receipt_input.replace('[','')
    receipt_input = receipt_input.replace(']','')
    ###
    # Extract totals, fees, tips, taxes
    ###
    not_people = tuple(all_money.loc[extracted['items']:]) # since each item is on its own line, the number of items is a good cutoff
    if len(not_people) == 5: # if there are only 5, then no delivery fee was included
        subtotal = not_people[0]
        tax_input = not_people[1]
        fees_input = not_people[2]
        tip_input = not_people[3]
        total = not_people[4]
        with col_extract:
            st.success("Data extracted!")
            extracted_col(extracted,all_money,not_people,receipt_input,names)            
    elif len(not_people) == 6: # delivery fee assumed to be included
        subtotal = not_people[0]
        tax_input = not_people[1]
        fees_input = not_people[2]
        fees_input += not_people[3]
        tip_input = not_people[4]
        total = not_people[5]
        with col_extract:
            st.success("Data extracted!")
            extracted_col(extracted,all_money,not_people,receipt_input,names)  
    elif len(not_people) == 3: # this was a pickup order, so no fees or tip
        subtotal = not_people[0]
        tax_input = not_people[1]
        fees_input = 0
        tip_input = 0
        total = not_people[2]
        with col_extract:
            st.success("Data extracted!")
            extracted_col(extracted,all_money,not_people,receipt_input,names) 
    else:
        import pandas as pd
        st.warning(f"Expected 5 or 6 nonFood items, but found {len(not_people)}. Try manual input instead!")
        with col_extract:
            st.warning("Something went wrong. Did I OCR right?")
            extracted_col(extracted,all_money,not_people,receipt_input,names, status = 'bad')           
          
    return receipt_input ,fees_input, tax_input, tip_input

def extracted_col(extracted,all_money,not_people,receipt_input,names, status = 'good'):
    import pandas as pd
    # present info
    combed_df = pd.DataFrame({
        "category":['num people', 'items'],
        "data":[extracted['participants'], extracted['items']]
    })
    # Append names
    for name in names:
        try:
            plural = ['s' if extracted[name]>1 else '']
            name_df = pd.DataFrame({
                "category":name,
                "data":[f'bought {extracted[name]} item{plural[0]}']})
            combed_df = combed_df.append(name_df)
        except:
            continue
    # Append prices
    all_money = all_money.reset_index()
    all_money.columns = ['index','data']
    all_money['category'] = 'price ' + all_money['index'].astype(str)
    all_money = all_money.drop("index",axis=1)
    combed_df = combed_df.append(all_money)
    
    st.write("__Detected info:__")
    
    if status == 'bad':
        st.write("__Detected fees and totals:__")
        not_people
    else:
        for i, row in combed_df.iterrows():
            if row['data'] == not_people[-1]: # find total
                row['category'] = 'total' # rename total
        if len(not_people) == 6: # all fees
            for i,row in combed_df.iterrows():
                if row['data'] == not_people[-2]:
                    row['category'] = 'tip'
                if row['data'] == not_people[-3]:
                    row['category'] = 'service fee'
                if row['data'] == not_people[-4]:
                    row['category'] = 'delivery fee'
                if row['data'] == not_people[-5]:
                    row['category'] = 'tax'
                if row['data'] == not_people[-6]:
                    row['category'] = 'subtotal'
            combed_df
        if len(not_people) == 5: # no delivery fee 
            for i,row in combed_df.iterrows():
                if row['data'] == not_people[-2]:
                    row['category'] = 'tip'
                if row['data'] == not_people[-3]:
                    row['category'] = 'service fee'
                if row['data'] == not_people[-4]:
                    row['category'] = 'tax'
                if row['data'] == not_people[-5]:
                    row['category'] = 'subtotal'
            combed_df
        if len(not_people) == 3: # no delivery fee, service fee, or tip
            for i, row in combed_df.iterrows():
                if row['data'] == not_people[-2]: # find tax
                    row['category'] = 'tax' # rename tax
                if row['data'] == not_people[-3]: # find subtotal
                    row['category'] = 'subtotal' # rename subtotal
            combed_df
    st.write("__Detected cost distribution:__")
    st.write(receipt_input.title())
    
def start(button=None):
    '''
    Main app. Creates the GUI and gathers basic info.
    '''
    if type(button) == str:
        pass
    
    st.title('Venmo Requests Calculator')
    direction = st.radio("Select input type", options=['Image','PDF (WIP)','Manual'])
    if direction == 'Manual':
        receipt_input ,fees_input, tax_input, tip_input = manual_input()

    elif direction == 'PDF (WIP)':
        receipt_input ,fees_input, tax_input, tip_input = auto_input('pdf')
    else:
        receipt_input ,fees_input, tax_input, tip_input = auto_input('image')

    ###
    # manual_input() was cut from here
    ###
    
    rf = receiptFormat()
    # a dictionary of name(s) and sum of amount
    raw_pairs = [(
            rf.parse_alpha(alpha),
            sum([float(i) for i in rf.parse_numbers(numbers)])
        ) for (alpha, numbers) in re.findall(rf.pattern, receipt_input)]
    # combine all split costs with the people involved
    data = {}
    for (people, amount) in raw_pairs:
        for person in [person.capitalize() for person in people]:
            if not person in data:
                data[person] = round(amount/len(people),2)
            else:
                data[person] += round(amount/len(people),2)

    precheck_sum = sum(data.values())
    total_value = round(precheck_sum+tax_input+tip_input+fees_input,2) # prefill the total

    total_input = st.number_input("Calculated Total*",step=10.0,value=total_value)

    try:
        # gets a dictionary of total spent, dictionary of spent on food, percent tip, percent tax, and misc fees per person
        my_total, my_food, tip_perc, tax_perc, fee_part = venmo_calc(my_dic = data, total=total_input, tax=tax_input, tip=tip_input, misc_fees=fees_input)

    ##### LIVE TESTING AREA #####

    except Exception as e:
        ''
    #############################
    # Database section
    
    st.write("Not required, but very fun")
    col_save,col_show = st.beta_columns([0.33,1])

    with col_show:
        button_show = st.button(label='Preview the Database')
    with col_save:
        button_save = st.button(label='Submit to Database')
    if button_save == True:
        saveus = saveInfo(my_total, my_food, tip_perc, tax_perc, fee_part,showme='no')
        saveus.save_table()
        st.balloons()

    if button_show == True:
        showus = saveInfo()
        dataframe = showus.read_table()
        dataframe = dataframe.iloc[:,1:]
        show_me = dataframe.tail()
        st.table(show_me)
            
def venmo_calc(my_dic, total, tax=0, tip=0, misc_fees=0):
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
        tip_perc = tip/(total-tip-misc_fees-tax)
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
        ### Explain the calculation for transparency ###
        with st.beta_expander(label='What just happened?'):
            st.write(f"""
            1. Tax% ($p_x$) was calculated using tax/(food_total): __{round(tax_perc*100,2)}%__
            2. Tip% ($p_p$) was calculated using tip/(food_total): __{round(tip_perc*100,2)}%__
            3. Fees were distributed equally: __${fee_part}__ per person
            4. Each person's sum was calculated using: $m_t=d_s + (d_s * p_x) + (d_s*p_p) + d_f$
                * $m_t$ = total money to request
                * $d_s$ = dollars spent on food
                * $p_x$ = percent tax
                * $p_p$ = percent tip
                * $d_f$ = dollars spent on fee
            """)
        rounded_sum = round(rounded_sum,2)
        ### Error catcher ###
        if (rounded_sum > total+0.1):
            return st.write(f"Uh oh! My calculated venmo charge sum is ${rounded_sum} but the receipt total was ${round(total,2)}")

        ### Format the output ###
        output_money = {}
        for key in request.keys():
            output_money[key] = [round(request[key],2)]
        df_out = pd.DataFrame.from_dict(output_money)
        df_out = df_out.reset_index(drop=True)
        df_out = df_out.T
        df_out.columns = ['Amount']

        venmo_request(request,my_dic,tip_perc,tax_perc,fee_part,tip,tax,misc_fees,df_out)

        return output_money, my_dic, tip_perc, tax_perc, fee_part

def venmo_request(request,my_dic,tip_perc,tax_perc,fee_part,tip,tax,misc_fees,df_out):
    '''
    Generates a link that directs user to venmo app with prefilled options

    ASCII table source: http://www.asciitable.com/
    Use Hx column, add a % before it
    '''
    # retained for posterity
#     html_table_style = '''
#     <style type="text/css">
#     .tg  {border-collapse:collapse;border-spacing:0;}
#     .tg td{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
#       overflow:hidden;padding:10px 5px;word-break:normal;}
#     .tg th{border-color:black;border-style:solid;border-width:1px;font-family:Arial, sans-serif;font-size:14px;
#       font-weight:normal wow this is impressive;overflow:hidden;padding:10px 5px;word-break:normal;}
#     .tg .tg-0pky{border-color:inherit;text-align:left;vertical-align:top}
#     </style>'''

    # used in venmo_request
    html_table_header = '''
    <table class="tg">
    '''
    # used in venmo_request
    html_table_end = '''</tr>
    </tbody>
    </table>'''
    link_output = {}

    for key in request.keys():
        txn = 'charge' # charge or pay
        audience = 'private' # private, friends, or public
        amount = round(request[key],2) # total requested dollars

        # statement construction
        statement = f'Hi {key}! Food was ${round(my_dic[key],2)}'
        if tip > 0.0:
            statement += f', tip was {round(tip_perc*100,2)}%25'
        if tax > 0.0:
            statement += f', tax was {round(tax_perc*100,2)}%25'
        if misc_fees > 0.0:
            statement += f', fees were {round(fee_part,2)}'

        statement += '.%0AMade with %3C3 at payme.peti.work' # %0A creates a new line
        statement = statement.replace(' ','%20') # replace spaces for url parameter
        link = f"https://venmo.com/?txn={txn}&audience={audience}&recipients={key}&amount={amount}&note={statement}"
        #link_html = f"<a href='{link}' target='_blank'>Click me for {key}'s sake!</a>"
        #link_md = f"[Click me for {key}'s sake!](link)"
        link_output[key] = link

    html_table_data = f'''
<tbody>'''
    venmo_logo = 'https://cdn1.venmo.com/marketing/images/branding/downloads/venmo_logo_blue.svg'

    for key in request.keys():
        # append each person's rows to html table 
        html_row = f'''
<tr>
    <td class="tg-0pky">{key}<br></td>
    <td class="tg-0pky">${round(request[key],2)}</td>
    <td class="tg-0pky"><a href="{link_output[key]}" target="_blank" rel="noopener noreferrer"><img src="{venmo_logo}" width="60"></a><br></td>
</tr>'''
        html_table_data += html_row

    html_table = html_table_header + html_table_data + html_table_end

    st.write(html_table, unsafe_allow_html=True)
    st.write('')

def app():
    '''
    Only purpose is to start the app. Own function so the rest of the functions can be organized in a logical way.
    '''
    start(button='start')
    
app()