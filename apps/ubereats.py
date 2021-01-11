import streamlit as st
import pandas as pd
import numpy as np # for nan

def extras_remover(my_dict, key, loc1):
    '''
    Removes extras by cutting out anything before a line consists of a single digit number.
    Single digit is assumed to be the number of meals bought
    
    input
    -----
    my_dict: dict
        Dictionary of name:series, where the series is a series of strings
    key: str
        Which name had the extra
    loc: int
        The loc where "extra" occured within the value's series
    '''
    og_series = my_dict[key]
    my_series = my_dict[key].loc[loc1:] # get everything after the extra
    
    # if there is a row with a single digit in it after the extras, 
    # then the extras is in between two meals
    if my_series.str.fullmatch("\d").sum() > 0:
        for i, v in my_series.items():
            extras_loc = []
            try:
                num_meals = int(v)
                if (num_meals >=1) & (num_meals <=9):
                    loc2 = i # location of 1
                    for i, v in my_series.loc[loc1:loc2-1].items():
                        extras_loc.append(i) # get the indexes of all items between loc and loc2
                    # drop everything at those indexes
                    og_series = og_series.drop(extras_loc)
            except:
                pass
    # if the series was passed here, it must have an extra somewhere
    # if no single digit found, then just cut everything off after the loc of extra
    else:
        og_series = og_series.loc[:loc1]
    return og_series

def name_maker(my_names):
    '''
    Formats user inputed names, and appends extras like total, subtotal, delivery fee, etc.
    '''
    my_names = my_names.split(',')
    # format input to remove space and make it all lowercase
    names = [n.lower().strip() for n in my_names]
    only_names = names.copy()
    names += ['subtotal','promotion','service', 'delivery', 'tip']
    names = tuple(names)
    names_dict = {} # dictionary of names and their iloc in the series
    names_dict['total'] = 0 # total is always the first line
    return names_dict, names, only_names

def receipt_formatter(receipt, names_dict, names):
    '''
    Eliminates all the extra fluff, retaining just the names and appropriate prices
    '''
    text_str = pd.Series(receipt.split('\n')) # split by new line
    # how many times does the word extras appear
    extras_num = receipt.count('extras')

    # find where each name occurs to infer what belongs to them
    for loc, string in text_str.iteritems():
        for name in names:
            if name in string:
                names_dict[name] = loc
    keys = list(names_dict.keys())

    # get range of locs, where loc1 is the already gotten loc
    # and loc2 is the next keys value
    names_range = {}
    for i in range(len(keys)):
        name = keys[i]
        loc1 = names_dict[name]
        try:
            name2 = keys[i+1]  
            loc2 = names_dict[name2]
        except:
            loc2 = len(text_str)-1
        names_range[name] = [loc1, loc2]


    # assign each line to a name
    names_str_items = {}
    for name, nums in names_range.items():
        names_str_items[name] = text_str.loc[nums[0]:nums[1]-1]

    # Check for extras
    # extras always come after the full price of one meal in each person
    # full meals are always preceded by the number of that meal
    for name, items in names_str_items.items():
        for loc, strings in items.items():
            if strings.count("extra") > 0: # if an extra occurs
                # call function, reassign the dict series with new, cropped series
                names_str_items[name] = extras_remover(names_str_items,name, loc)


    # extract only the prices from each line
    names_prices = {}
    for name, data in names_str_items.items():
        my_data = data.str.extract('\$(\d+\.\d+)')
        my_data = my_data.dropna()[0]
        names_prices[name] = list(pd.to_numeric(my_data))

    # make promotion negative
    names_prices['promotion'][0] = names_prices['promotion'][0] * -1
    return names_prices

def sanity_check(names_prices):
    '''
    Confirms with the user that the calculated total is equal to the actual total.
    If True, script continues.
    If False, script stops.
    '''
    #### SANITY CHECK ####
    total = 0
    for k, v in names_prices.items():
        if k not in 'subtotal':
            total += sum(names_prices[k])

    st.info(f"The total paid was __${total}__, is this correct?")
    sanity_check = st.radio("",["Yes","No"])
    if "no" in sanity_check.lower():
        st.warning("Sorry about that, try the manual or OCR options.")
        st.write("Here's what I found:")
        # show our output for future feedback
        # Let user edit the df as needed!
        max_len = 0
        for k,v in names_prices.items():
            if len(v) > max_len:
                max_len = len(v)
        for k,v in names_prices.items():
                if len(v) < max_len:
                    v.append(np.nan) # to make all lists same size for df
        st.table(pd.DataFrame(names_prices).T)
        st.stop()
    else:
        letsgo = True
        return
        
    return letsgo

def receipt_for_machine(my_dict, description, only_names):
    '''
    Formats a dictionary of prices to be compatible with the rest of the payme script
    '''
    fees_input = 0
    tax_input = 0
    tip_input = 0
    receipt_input = ''
    # divide promotion by the number of people
    equal_promos = my_dict['promotion'][0]/len(only_names)

    for name, values in my_dict.items():
        if name not in only_names:
            if (name == 'service') or (name == 'delivery'):
                fees_input += values[0]
            if name == 'tip':
                tip_input += values[0]
        else:
            # account for promo in sum
            fair_value = sum(values) + equal_promos
            standardized = f"{name}: {fair_value}"
            receipt_input += standardized
    # Deduct the promotion from fees
    return_me = {}
    return_me['description'] = description
    return_me['receipt_input'] = receipt_input
    return_me['fees_input'] = fees_input
    return_me["tax_input"] = tax_input # always 0 in mexico, VAT is included
    return_me['tip_input'] = tip_input
    
    return return_me
    


def app():
    '''
    Main region of uber eats parser
    '''
    with st.beta_expander("How To"):
        st.write("""
        1. Type in the restaurants name.
        2. Copy and paste the entire contents of UberEats receipt from the *Total* at the top to final charge at the bottom.
        3. Type in the names of everyone that appears on the receipt, separated by commas.
        4. Confirm the total is correct.
        """)
    ### GUI ###
    description = st.text_input("(Optional) Description, like the restaurant name")
    receipt = st.text_area("Paste the entire receipt from UberEats below, including totals and fees")
    receipt = receipt.lower()
    receipt = receipt.replace(',','')
    if receipt:
        my_names = st.text_input("Add names below, separated by a comma. Ex: peter, Russell")
    if not receipt:
        st.stop()
    if not my_names:
        st.stop()
        
    # Get the names, adds additional variables like total, tip, fees, etc
    names_dict, names, only_names = name_maker(my_names)
    # Assign prices to each variable, eliminate extras
    names_prices = receipt_formatter(receipt, names_dict, names)
    # Confirm with user total is correct
    sane = sanity_check(names_prices)
    if sane == False:
        st.stop()
    # standardize output for rest of script    
    return_me = receipt_for_machine(names_prices, description, only_names)
    
    return return_me
