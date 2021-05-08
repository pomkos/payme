# content creator, including price splitting, text formatting, message creating

import streamlit as st
import re
import requests as r # for rebrandly api
import json # for rebrandly api
import pandas as pd


def currency_converter(my_dic, total, tax, tip, misc_fees, contribution, discount):
    '''
    Converts from local currency to USD
    
    input
    -----
    my_dic: dict
        Dictionary of name: prices
    total: float
    tax: float
    tip: float
    misc_fees: float
    contribution: float
    discount: float
    
    return
    ------
    All of the above, but with converted currency
    '''
    # Get currency info
    from apps import db_tool
    c = db_tool.getCurrency()
    df = c.df
    options = df['country'].sort_values().reset_index(drop=True)
    ctry = st.selectbox('Select country', options=options, index=17)
    usd_convert = list(df[df['country']==ctry]['rate'])[0] # get rate from db
    symbol = list(df[df['country']==ctry]['code'])[0]
    
    # Convert prices
    for name, price in my_dic.items():
        my_dic[name] = price/usd_convert
    discount = discount/usd_convert
    total = round(total/usd_convert,2)
    tax = tax/usd_convert
    tip = tip/usd_convert
    misc_fees = misc_fees/usd_convert
    contribution = contribution/usd_convert
    
    # To construct webgui info
    date = df['date_updated'][0].date()
    usd_convert_type = f'{round(usd_convert,2)} {symbol}'
    convert_info = [usd_convert_type, date]
    
    return my_dic, total, tax, tip, misc_fees, discount, contribution, convert_info

    

def venmo_calc(my_dic, total, description, discount=0 ,tax=0, tip=0, misc_fees=0, convert=False, contribution=0):
    """
    Returns lump sums to request using venmo

    input
    -----
    my_dic: dict
        Dictionary of name: sum of itemized food prices
    total: float
        Total shown on receipt, charged to your card
    tax: float
        Tax applied in dollars, not percent
    tip: float
        Amount tipped in dollars, not percent
    misc_fees: float
        Sum of all other fees not accounted for, like delivery fee, etc
    mess: bool
        Whether the message should be clean or a prefilled venmo link
    output
    -----
    data: list
        List including all of the below variables:
        -------------------
        request_money: dict
            Dictionary of name: amount to request, rounded to 2 digits
        tip_perc: float
            Percent tipped. Used to calculate request_money. Not rounded
        tax_perc: float
            Percent taxed. Used to calculate request_money. Not rounded
        fee_part: float
            Total fees charged to each person. Used to calculate request_money. Rounded to 2 digits
        messages: dict
            Dictionary of name:message, where the message is either clean (for use with venmo api),
            or a venmo link (user clicks it and opens the app, prefilled)
        -------------------
    """
    total = round(total,2) # otherwise get weird 23.00000005 raw totals
    
    ###### Currency to USD conversion ######
    convert = st.checkbox("Convert to USD") # ask if MXD or USD is required
    if convert:
        my_dic, total, tax, tip, misc_fees, discount, contribution, usd_convert = currency_converter(my_dic, total, tax, tip, misc_fees, contribution, discount)
    ########################################
    
    precheck_sum = round(sum(my_dic.values())+tax+tip+misc_fees+discount+contribution,2)
    # Just a quick precheck to make sure manual input was correct
    if total != precheck_sum:
        st.error(f"You provided {total} as the total, but I calculated {precheck_sum}")
        st.stop()
    else:
        num_ppl = len(my_dic.keys())
        tax_perc = tax/(total-tip-misc_fees-tax-discount-contribution)
        tip_perc = tip/(total-tip-misc_fees-tax-discount-contribution)
        store_perc = contribution/(total-tip-misc_fees-tax-discount-contribution)
        fee_part = round(misc_fees/num_ppl,2)
        disc_part = round(discount/num_ppl,2)
        request = {}
        rounded_sum = 0
                
        for key in my_dic.keys(): 
            my_total = my_dic[key]
            tax_part = tax_perc * my_total
            tip_part = tip_perc * my_total
            store_part = store_perc * my_total

            person_total = my_total + tax_part + fee_part + tip_part + disc_part + store_part
            rounded_sum += person_total
            request[key] = person_total
            
        ### Dynamically explain the calculation for transparency ###
        formula = """
1. Each person's sum was calculated using: $m_t = d_s"""
        
        formula_key = """
    * $m_t$ = total money to request
    * $d_s$ = dollars spent on food"""
        steps = '''
        
        '''
        
        #############
        #    TAX    #
        #############
        if tax_perc > 0:
            formula += " + (d_s * p_x)"
            formula_key += """
    * $p_x$ = percent tax"""
            steps += f"""
2. Tax% ($p_x$) was calculated using {round(tax,2)}/({round(total,2)}-{round(tip,2)}-{round(tax,2)}-{round(misc_fees,2)}-({round(discount,2)})): __{round(tax_perc*100,2)}%__
            """
        ##############
        # TIP DRIVER #
        ##############
        if tip_perc > 0:
            formula += " + (d_s*p_d)"
            formula_key += """
    * $p_d$ = percent tip to driver"""
            steps += f"""
2. Tip to the driver ($p_p$) was calculated using {round(tip,2)}/({round(total,2)}-{round(tip,2)}-{round(tax,2)}-{round(misc_fees,2)}-({round(discount,2)})): __{round(tip_perc*100,2)}%__
            """
        #############
        # TIP STORE #
        #############
        if (contribution > 0):
            formula += " + (d_s * p_r)"
            formula_key += """
    * $p_r$ = percent tip to restaurant"""
            steps += f"""
2. Tip to the restaurant ($p_r$) was calculated using {round(contribution,2)}/({round(total,2)}-{round(tip,2)}-{round(contribution,2)}-{round(tax,2)}-{round(misc_fees,2)}-({round(discount,2)})): __{round(store_perc*100,2)}%__
            """
        #############
        #    FEES   #
        #############
        if misc_fees > 0:
            formula += " + d_f"
            formula_key += """
    * $d_f$ = dollars spent on fee"""
            steps += f"""
2. Fees were distributed equally: __${round(fee_part,2)}__ per person
            """  
        #############
        # DISCOUNT  #
        #############
        if (discount != 0):
            formula +=  "- d_d"
            formula_key += """
    * $d_d$ = discount"""
            steps += f"""
2. The discount was distributed equally: deducted __${round(disc_part,2)}__ from each person"""
        #############
        # CURRENCY  #
        #############
        if convert:
            steps += f"""
2. All tax, tip, fees, totals were converted to USD. __1 USD = {usd_convert[0]}__.
    * The rate was last updated on {usd_convert[1]} using information provided by [RatesAPI](https://ratesapi.io/)
            """
        # put it all together
        this_happened = formula + "$" + formula_key + steps
        
        with st.beta_expander(label='What just happened?'):
            st.write(this_happened)
        rounded_sum = round(rounded_sum,2)
        ### Error catcher ###
        if (rounded_sum > total+0.1):
            st.error(f"Uh oh! My calculated venmo charge sum is ${rounded_sum} but the receipt total was ${round(total,2)}, a difference of ${round(abs(rounded_sum-total),2)}")
            st.stop()

        ### Round the calculated request amounts ###
        request_money = {}
        for key in request.keys():
            request_money[key] = [round(request[key],2)]
        from apps import manual_mode as mm
        # get dictionary of name:message

        # gather variables for **kwarg
        for_messages = {
            'description':description,
            'request':request_money,
            'my_dic':my_dic,
            'tip_perc':tip_perc,
            'store_perc':store_perc,
            'tax_perc':tax_perc,
            'fee_part':fee_part,
            'misc_fees':misc_fees,
            'disc_part':disc_part,
            'convert':convert
        }
        if convert:
            for_messages['convert_info'] = usd_convert

        messages = venmo_message_maker(**for_messages)
        
        data = {"request_money":request_money,
                "messages":messages}       
        return data
    
def venmo_message_maker(description,request,my_dic,tip_perc,tax_perc,fee_part,misc_fees,disc_part, store_perc, convert, convert_info=''):
    '''
    Generates a message or link that directs user to venmo app with prefilled options
    '''
    link_output = {}
    message_output = {}
    import urllib.parse
    for key in request.keys():
        txn = 'charge' # charge or pay
        audience = 'private' # private, friends, or public
        amount = request[key] # total requested dollars

        # statement construction
        # ﹪ is required instead of % because of a bug in venmo note
        statement = f'''👋 Aloha {key}!
Your total '''
        if description:
            statement+= f'at {description.title()} '
        statement+= f'was ${round(my_dic[key],2)}'
        if tip_perc > 0.0:
            statement += f', tip to driver or wait staff was {round(tip_perc*100,2)}﹪'
        if store_perc > 0.0:
            statement += f', tip to establishment was {round(store_perc*100,2)}﹪'
        if tax_perc > 0.0:
            statement += f', tax was {round(tax_perc*100,2)}﹪'
        if misc_fees > 0.0:
            statement += f', fees were ${round(fee_part,2)}'
        if abs(disc_part) > 0.0:
            statement += f', your discount was ${round(disc_part,2)}'
        if convert:
            statement += f"""
Everything was converted as 1 USD = {convert_info[0]}"""
        statement += f'''.
        
Made with ❤️ at payme.peti.work''' # %0A creates a new line
        statement = urllib.parse.quote(statement)
        message_output[key] = statement # stores message only, no venmo link
        
        # "&not" gets converted to a weird notation, not interpreted by ios. Use "&amp;" to escape the ampersand
        # took out recipients={key}&amp; so recipients dont get autofilled. Doesn't work in iOS or Android.
        link = f"https://venmo.com/?txn={txn}&amp;audience={audience}&amp;amount={amount[0]}&amp;note={statement}"
        link_output[key] = link

    return link_output
    
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

def total_calculator(description, receipt_input, fees_input, tax_input, tip_input, discount, contribution=0):
    """
    Calculates the total amount spent using all variables. Separated function so we can take account for params in future
    """
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
            if not person in data: # then its a fee or total
                data[person] = round(amount/len(people),2)
            else:
                data[person] += round(amount/len(people),2)
    precheck_sum = sum(data.values())
    total_value = round(precheck_sum+tax_input+tip_input+fees_input+discount+contribution,2) # prefill the total
    total_input = st.number_input("Calculated Total*",step=10.0,value=total_value)
    return total_input, data


def link_shortener(my_string):
    '''
    Shortens links using the rebrandly api
    '''
    try:
        access_token = pd.read_csv('data/secret.csv').iloc[0,0]
    except:
        st.error("Tell Pete to import the rebrandly secrets")
        return my_string
    
    linkRequest = {
      "destination": f"{my_string}"
      , "domain": { "fullName": "clickme.peti.work" }
    }

    requestHeaders = {
      "Content-type": "application/json",
      "apikey": f"{access_token}",
    }

    response = r.post("https://api.rebrandly.com/v1/links", 
        data = json.dumps(linkRequest),
        headers=requestHeaders)

    if (response.status_code == r.codes.ok):
        short_link = response.json()['shortUrl']
        return short_link
    else:
        st.error("Tell Pete to update the rebrandly secrets")
        st.error(response.status_code)
        return my_string

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
        link = link_shortener(link_output[key])
        # append each person's rows to html table 
        html_row = f'''
        <tr>
            <td class="tg-0pky">{key}<br></td>
            <td class="tg-0pky">${request_money[key][0]}</td>
            <td class="tg-0pky"><a href="{link}" target="_blank" rel="noopener noreferrer"><img src="{venmo_logo}" width="60" ></a><br></td>
        </tr>'''
        html_table_data += html_row
        
        copy_str = f"""**{key}**: {link} \n"""
        copy_me += copy_str
    html_table_all = html_table_header + html_table_data + html_table_end
    
    # get the request links
    if "request" in link_type.lower():
        st.write(html_table_all, unsafe_allow_html=True)
        copy_to_clipboard(copy_me) # copy button
        
    # get the pay links
    else:
        html_table_all = html_table_all.replace("charge","pay")

        copy_me = copy_me.replace("charge","pay")

        st.write(html_table_all, unsafe_allow_html=True)
        copy_to_clipboard(copy_me) # copy button

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