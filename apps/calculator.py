# content creator, including price splitting, text formatting, message creating

import streamlit as st
import pandas as pd
import numpy as np
import re
import sys

def currency_converter(my_dic, total, tax, tip, misc_fees):
    '''
    Converts from local currency to USD
    '''
    
    usd_convert = 20.12 # 1usd is 20.12 peso as of Jan 10, 2020
    for name, price in my_dic.items():
        my_dic[name] = price/usd_convert
    total = round(total/usd_convert,2)
    tax = tax/usd_convert
    tip = tip/usd_convert
    misc_fees = misc_fees/usd_convert
    
    return my_dic, total, tax, tip, misc_fees

    

def venmo_calc(my_dic, total, description, tax=0, tip=0, misc_fees=0, clean=False):
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
    
    ###### MXD to USD conversion ######
    convert = st.checkbox("Convert MXD to USD") # ask if MXD or USD is required
    if convert:
        my_dic, total, tax, tip, misc_fees = currency_converter(my_dic, total, tax, tip, misc_fees)
    ###################################
    
    precheck_sum = round(sum(my_dic.values())+tax+tip+misc_fees,2)
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
        this_happened = f"""
            1. Tax% ($p_x$) was calculated using {round(tax,2)}/({round(total,2)}-{round(tip,2)}-{round(tax,2)}-{round(misc_fees,2)}): __{round(tax_perc*100,2)}%__
            2. Tip% ($p_p$) was calculated using {round(tip,2)}/({round(total,2)}-{round(tip,2)}-{round(tax,2)}-{round(misc_fees,2)}): __{round(tip_perc*100,2)}%__
            3. Fees were distributed equally: __${round(fee_part,2)}__ per person
            4. Each person's sum was calculated using: $m_t=d_s + (d_s * p_x) + (d_s*p_p) + d_f$
                * $m_t$ = total money to request
                * $d_s$ = dollars spent on food
                * $p_x$ = percent tax
                * $p_p$ = percent tip
                * $d_f$ = dollars spent on fee
                
            """
        if convert:
            this_happened += "5. All tax, tip, fees, totals were converted to USD. __1 USD = 20.12 MXD__"
        with st.beta_expander(label='What just happened?'):
            st.write(this_happened)
        rounded_sum = round(rounded_sum,2)
        ### Error catcher ###
        if (rounded_sum > total+0.1):
            return st.write(f"Uh oh! My calculated venmo charge sum is ${rounded_sum} but the receipt total was ${round(total,2)}")

        ### Round the calculated request amounts ###
        request_money = {}
        for key in request.keys():
            request_money[key] = [round(request[key],2)]
        from apps import manual_mode as mm
        # get dictionary of name:message
        messages = venmo_message_maker(description,request_money,my_dic,tip_perc,tax_perc,fee_part,tip,tax,misc_fees, clean_message=clean)
        
        data = {"request_money":request_money,
                "messages":messages}       
        return data
    
def venmo_message_maker(description,request,my_dic,tip_perc,tax_perc,fee_part,tip,tax,misc_fees, clean_message=False):
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
        statement = f'Hi {key}! Food '
        if description:
            statement+= f'at {description.title()} '
        statement+= f'was ${round(my_dic[key],2)}'
        if tip > 0.0:
            statement += f', tip was {round(tip_perc*100,2)}{urllib.parse.quote("﹪")}'
        if tax > 0.0:
            statement += f', tax was {round(tax_perc*100,2)}{urllib.parse.quote("﹪")}'
        if misc_fees > 0.0:
            statement += f', fees were ${round(fee_part,2)}'

        statement += f'.%0AMade with {urllib.parse.quote("❤️")} at payme.peti.work' # %0A creates a new line
        statement = statement.replace(' ','%20') # replace spaces for url parameter
        message_output[key] = statement # stores message only, no venmo link
        
        # "&not" gets converted to a weird notation, not interpreted by ios. Use "&amp;" to escape the ampersand
        link = f"https://venmo.com/?txn={txn}&amp;audience={audience}&amp;recipients={key}&amp;amount={amount[0]}&amp;note={statement}"
        link_output[key] = link

    if clean_message:
        return message_output
    else:
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

def total_calculator(description, receipt_input, fees_input, tax_input, tip_input):
    """
    Calculates the total amount spent using all variables. Separated function so we can take account for params
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
            if not person in data:
                data[person] = round(amount/len(people),2)
            else:
                data[person] += round(amount/len(people),2)

    precheck_sum = sum(data.values())
    total_value = round(precheck_sum+tax_input+tip_input+fees_input,2) # prefill the total
    total_input = st.number_input("Calculated Total*",step=10.0,value=total_value)
    
    return total_input, data