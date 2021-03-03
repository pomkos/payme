import streamlit as st
import pandas as pd

# GUI for manual input option
def manual_input(gui, params):
    '''
    Thalamus. Redirects to doordash, ubereats, or manual input
    '''
    if params:
        total_inputp, datap, tax_inputp, fees_inputp, tip_inputp, sharep = params
        
    else:
        total_inputp=0.0
        datap=''
        describep=''
        tax_inputp=0.0
        fees_inputp=0.0
        tip_inputp=0.0
        sharep=False
        
    if "delivery" in gui.lower():
        return delivery_mode()
    else:
        return manual_mode()

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

def delivery_mode():
    ##########
    # HOW TO #
    ##########
    st.title("Venmo Requests Calculator: Delivery App Mode")
    st.write("Give us the DoorDash or UberEats receipt, we'll spit out some venmo request links!")
    with st.beta_expander("How To"):
        col1,col2 = st.beta_columns(2)
        with col1:
            st.write("""
            __DoorDash__

            1. Copy and paste the entire contents of DoorDash receipt from __Order Details__ at the top to the __Total__ at the bottom.
            2. Follow the prompts """)
            st.write("")
            st.markdown("![DoorDash copy instructions](https://github.com/pomkos/payme/raw/main/images/copy_dd.gif)")
        with col2:
            st.write("""
            __UberEats__

            1. Copy and paste the entire contents of UberEats receipt from __Total__ at the top to __Tip__ at the bottom.
            2. Once pasted, make sure names are on separate lines.
            3. Follow the prompts""")
            st.write("")
            st.markdown("![UberEats copy gif placeholder](https://github.com/pomkos/payme/raw/main/images/copy_ue.gif)")
    #######
    # GUI #
    #######
    description = st.text_input("(Optional) Description, like the restaurant name")
    receipt = st.text_area("Paste the entire receipt from your service, including totals and fees", height = 300)
    receipt = receipt.lower()

    if not receipt:
        st.info("See the how to for more information!")
        st.stop()

    #########
    # LOGIC #
    #########
    try:
        if "(you)" in receipt.lower(): # ubereats has this
            st.info("This looks like an UberEats receipt.")
            deny = st.checkbox("It's actually DoorDash")
            if deny:
                service_chosen = 'doordash'
            else: #its ubereats
                service_chosen = 'ubereats'
                receipt = receipt.replace(',','')
        elif "participant" in receipt: # doordash
            st.info("This looks like a DoorDash receipt.")
            deny = st.checkbox("It's actually UberEats")
            if deny:
                service_chosen = 'ubereats'
            else:
                service_chosen = 'doordash'
        else:
            st.error("Unknown delivery app. See the how to, try the manual mode, or contact Pete to request support for the receipt!")
            st.stop()
        my_names = name_finder(receipt)
        service_chosen = service_chosen.lower()
        if 'door' in service_chosen:
            from apps import doordash as dd
            user_output = dd.app(receipt, my_names, description)
        elif 'uber' in service_chosen:
            from apps import ubereats as ue
            user_output = ue.app(receipt, my_names, description)
        return user_output
    except Exception as e:
        st.write(e)
        st.stop()
        
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
    col1, col2 = st.beta_columns(2)
    col3, col4 = st.beta_columns(2)

    with col1:
        fees_input = st.number_input("Fees in dollars",step=1.0)
    with col2:
        tax_input = st.number_input("Tax in dollars",step=1.0)
    with col3:
        tip_input = st.number_input("Tip in dollars",step=5.0)
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

def copy_to_clipboard(text):
    '''
    Copies anything in the textbox to clipboard.
    '''
    import streamlit as st
    from bokeh.models.widgets import Button
    from bokeh.models import CustomJS
    from streamlit_bokeh_events import streamlit_bokeh_events
    from io import StringIO
    import pandas as pd
    import js2py
    import streamlit.components.v1 as components
    
    # button styling, function. Textarea content, location.
    input_ =f'''<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
    
    <button class="btn btn-outline-info" onclick="myFunction()">Copy</button>
    
    <div>
    <textarea id="myInput" cols=28 style="position:absolute; left: -10000px;">{text}</textarea>
    </div>
    '''
    
    # f string so links can be added to textbox
    html_first = f"""<script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" 
                        integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" 
                        crossorigin="anonymous"></script> 
                        {input_}
                    """
    
    # second part of html code, brackets wont allow it to be part of fstring
    html_second = """
    <SCRIPT LANGUAGE="JavaScript">
    function myFunction(){
    var copyText = document.getElementById("myInput");
    copyText.select();
    copyText.setSelectionRange(0, 99999); 
    document.execCommand("copy");
    }
    </SCRIPT>
    """
    # add strings together to get full html code
    html_all = html_first + html_second
    # pass it to components.html
    html_code = components.html(html_all, height=50)
    # add to page
    
    html_code
    
def replace_recip(my_string,venmo_user):
    "Replaces recipient with the given venmo username"
    import re
    new_string = re.sub("recipients=([A-Z])\w+&",f"recipients={venmo_user}&",my_string)
    return new_string
    
def html_table(link_output, request_money):
    '''
    Presents name, amount, and custom venmo link in a sweet table
    ASCII table source: http://www.asciitable.com/
    Use Hx column, add a % before it
    '''
    link_type = st.selectbox("Request payments yourself, or send payme links to your friends", options=['Request them', 'Pay me'])
    
    html_table_header = '''
    <table class="tg">
    '''
    html_table_end = '''</tr>
    </tbody>
    </table>'''
    
    html_table_data = f'''<tbody>'''    
    venmo_logo = 'https://raw.githubusercontent.com/pomkos/payme/main/images/venmo_logo_blue.png'
    
    copy_me = ''
    for key in link_output.keys():
        # append each person's rows to html table 
        html_row = f'''
        <tr>
            <td class="tg-0pky">{key}<br></td>
            <td class="tg-0pky">${request_money[key][0]}</td>
            <td class="tg-0pky"><a href="{link_output[key]}" target="_blank" rel="noopener noreferrer"><img src="{venmo_logo}" width="60" ></a><br></td>
        </tr>'''
        html_table_data += html_row
        
        copy_str = f"""**{key}**: {link_output[key]} \n"""
        copy_me += copy_str
    html_table_all = html_table_header + html_table_data + html_table_end
    
    # get the request links
    if "request" in link_type.lower():
        st.write(html_table_all, unsafe_allow_html=True)
        copy_to_clipboard(copy_me) # copy button
    # get the pay links
    else:
        # v_user = st.text_input("Your venmo username")  # didnt wanna dig into code, but this doesn't work
        v_user = ''
        if v_user:
            html_table_all = html_table_all.replace("charge","pay")
            html_table_all = replace_recip(html_table_all,v_user)
            
            copy_me = copy_me.replace("charge","pay")
            copy_me = replace_recip(copy_me,v_user)
            
            st.write(html_table_all, unsafe_allow_html=True)
            copy_to_clipboard(copy_me) # copy button

