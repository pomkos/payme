"""
Starts a streamlit script to allow people to select which foods they bought. For use with payme.
"""

import streamlit as st
import numpy as np
import pandas as pd
import sqlalchemy as sq
import streamlit_analytics

engine = sq.create_engine("sqlite:///data/food.db")
cnx = engine.connect()

do = st.sidebar.radio("",options=['Sort food','Add receipt'])

def name_chooser(df_saved):
    '''
    Eliminates names that already occurred in the db
    '''
    all_names = ["Peter", "Matt", "Steve", "Aron", "Julie", "Grace", "Russell"]
    # theres a bug where removing the name from names when names is the iteree,
    # 
    names = []
    # remove names and meals from options if already in db
    for name in all_names:
        if name not in list(df_saved["name"].unique()):
            names.append(name)
    names.sort()
    all_names.sort()
    return all_names

def meal_chooser(df_saved, food_dict):
    '''
    Eliminates meals that are in db + have been accounted for
    '''
    # number of times each meal was claimed
    all_meals = [x.capitalize() for x in food_dict.keys()]
    meals = all_meals.copy()
    for meal in all_meals:
        if meal in df_saved["food"].unique():
            meal_df = df_saved[df_saved["food"] == meal]  # isolate df to just meal
            amount_claimed = meal_df["amount"].sum()  # num times it was bought
            if amount_claimed >= food_dict[meal.lower()][1]:
                # if we reached how many times meal was bought, remove
                # meal from available options
                meals.remove(meal)

    meals.sort()
    return meals

def info_gather(names, meals, df_saved, food_dict):
    '''
    Gathers info from user
    '''
    # gather user info
    name = st.selectbox("Name", options=names)
    colo, cola = st.beta_columns(2)
    with colo:
        order = st.selectbox("Select an order", options=meals)
    num_item = float(food_dict[order.lower()][1])
    with cola:
        amount = st.number_input("How much? (Ex: 1, 2, 0.5)", step=1.0, max_value=num_item, min_value=0.0)

    return name, order, amount

def food_df_to_dict(dataframe):
    '''
    Creates a dictionary out of a dataframe, with the "item" column as keys
    '''
    my_dict = {}
    new_df = dataframe.groupby('item').sum()
    for item in new_df.index:
        my_dict[item] = [new_df.loc[item,'price'],new_df.loc[item,'amount']]
    return my_dict

def sort_food():
    with st.beta_expander("How to"):
        st.write("""
        1. Choose name
        1. Choose a food item
        1. Enter how many of that meal you had.
        1. Use fractions to indicate shared orders. 0.33 if split by three, 0.5 if split by two, etc.
        1. If everything looks good click `Confirm and Submit`
        """)

    # dictionary where keys are the food, values are a list of [price, num_ordered]
    data = pd.read_sql("receipt",con=cnx)
    data2 = data[data['id'] >= 0.8887]
    food_dict = food_df_to_dict(data2)
    
    
    
#     food_dict = {
#         "drink: infused shot (13)": [6, 13],
#         "drink: lavender fusion (2)": [9, 2],
#         "drink: moskow mule (1)": [9, 1],
#         "meal: eggplant appetizer (2)": [8, 2],
#         "meal: vareniki + potato and mushrooms (2)": [17, 2],
#         "meal: fresh red salmon caviar karat (1)": [35, 1],
#         "meal: blini with stuffing (salmon) (1)": [12, 1],
#         "meal: classical julienne, plain (1)": [14, 1],
#         "meal: russian pelmeni + beef and pork (1)": [18, 1],
#         "meal: chicken tabaka (1)": [21, 1],
#         "meal: tandoori large plate (1)": [69.99, 1],
#         "drink: martini infused + apple and cinnamon (1)": [12, 1],
#         "dessert: halva (4)": [4.5, 4],
#         "dessert: kiev cake (1)": [8, 1],
#         "dessert: napoleon cake (1)": [7,1],
#         "dessert: medovik cake (1)": [8,1]
#     }

#     subtotal = 378.99
#     mb_sales_tax = 9.65
#     sales_tax = 20.46
#     total_tax = mb_sales_tax + sales_tax
#     sales_tax_perc = total_tax/subtotal
#     tip = 81.82
#     tip_perc = tip / subtotal
#     total = 490.92

    tip = food_dict['tip'][0]
    subtotal = food_dict['subtotal'][0]
    tip_perc = tip / subtotal
    sales_tax_perc = round(food_dict['tax'][0] / subtotal,2)

    try:
        df_saved = pd.read_sql("food", cnx)
    except:
        st.warning("Could not read database, initializing new one")
        df_saved = pd.DataFrame(
            {
                "name": ["test"],
                "food": ["test"],
                "price": [5.99],
                "amount": [2],
                "total_item_price": [5.99 * 2],
            }
        )
    streamlit_analytics.start_tracking()

    names = name_chooser(df_saved)
    meals = meal_chooser(df_saved, food_dict)

    name, order, amount = info_gather(names, meals, df_saved, food_dict)
    ph = st.empty()

    if not amount or not order or not name:
        st.info(
            "Select the food you ordered or shared, and write the amount of each. If shared, use fractions."
        )
        with ph.beta_container():
            st.write("__Current Database__")
            st.table(df_saved)
        st.stop()

    # format inputs
    price = food_dict[order.lower()][0]

    # prettify inputs for user's benefit

    receipt_df = pd.DataFrame(
        {
            "name": [name],
            "food": [order],
            "price": [food_dict[order.lower()][0]],
            "amount": [amount],
        }
    )

    receipt_df["total_item_price"] = receipt_df["amount"] * receipt_df["price"]

    # calculate and present user's taxes, tips, subtotal, total
    user_subtotal = sum(receipt_df["total_item_price"])
    with ph.beta_container():
        st.write("__Your item__")
        st.table(receipt_df)

    total = user_subtotal + (user_subtotal * sales_tax_perc) + (user_subtotal * tip_perc)
    st.info(
        f"""
    * Tax was {sales_tax_perc * 100}%, tip was {round((tip/subtotal) * 100,1)}%
    * Your subtotal is ${user_subtotal}
    * With tip and tax this meal cost ${round(total,2)}"""
    )

    # add to db
    submit = st.button("Confirm and Submit")
    if submit:
        try:
            df_saved = df_saved.append(receipt_df)
            with ph.beta_container():
                st.write("__New Database__")
                st.table(df_saved)
            df_saved.to_sql("food", cnx, if_exists="replace", index=False)
            st.success("Saved to db!")
        except:
            st.error("Couldn't save to db, tell Pete")
    streamlit_analytics.stop_tracking()

class receiptReceiver:
    def __init__(self):
        '''
        Class of functions to add receipt info so it can be sorted by users in the sort_food() function
        '''
        try:
            r_df = pd.read_sql("receipt",cnx)
            receipt = r_df['date'] == str(dt.datetime.now().date())
            #receipt = pd.DataFrame(columns = r_df.columns)
        except:
            receipt = pd.DataFrame(columns = ['food','price','amount','date'])
            
        self.receipt = receipt
        self.add_meals()
        
    def add_meals(self):
        '''
        Creates meals
        '''
        st.info("""Step 1. Add the meals using the format `burger: 15.81, 4`
* The first number represents how much one meal cost
* The second number represents how many times that meal was purchased""")
        receipt = st.text_area("One meal info per line")
        
        if not receipt:
            st.stop()
        
        df = self.detail_meals(receipt)
        df = self.add_fees(df)
        self.save_df(df)
        

    def detail_meals(self, receipt):
        '''
        Extracts costs for each meal
        '''
        r_list = receipt.split('\n')
        food_lst = [food.split(":")[0].strip() for food in r_list]
        money_lst = [food.split(":")[1].strip() for food in r_list]
        price_lst = [float(food.split(",")[0].strip()) for food in money_lst]
        amount_lst = [float(food.split(",")[1].strip()) for food in money_lst]
        
        df = pd.DataFrame({
            'item':food_lst,
            'price':price_lst,
            'amount':amount_lst
        })
        st.table(df)
        return df
    
    def add_fees(self, dataframe):
        '''
        Has user add taxes, fees, etc.
        '''
        subtotal = sum(dataframe['price'] * dataframe['amount'])
        st.write(f"Subtotal is ${subtotal}")
        st.info("Step 2. Add fees, taxes, gratuity")
        
        col_tax, col_tip = st.beta_columns(2)
        with col_tax:
            tax = st.number_input("Taxes ($)",step=1.0)
        with col_tip:
            tip = st.number_input("Tip ($)", step=1.0)
        fees = st.number_input("Fee ($)", step=1.0)
        if not tip:
            st.stop()
        total = subtotal + tax + tip + fees
        st.write(f"Total charged is to card is: ${round(total,2)}")
        
        dataframe = dataframe.append(pd.DataFrame({
            'item':['tax','tip','fees','subtotal','total'],
            'price':[tax, tip, fees, subtotal, total],
            'amount':[0,0,0,0,0]
        }))
        
        return dataframe
    
    def save_df(self, dataframe):
        '''
        Saves user created info
        '''
        st.info("Step 3. Confirm and submit!")
        st.table(dataframe)
        if not st.button("Save to Database"):
            st.stop()
        import datetime as dt
        dataframe['id'] = np.random.random()
        dataframe['date'] = str(dt.datetime.now().date())
        
        try:
            old_df = pd.read_sql("receipt", con=cnx)
            old_df = old_df.append(dataframe)
            old_df.to_sql("receipt", con=cnx, index=False, if_exists="replace")
            st.success("Saved!")
        except:
            dataframe.to_sql("receipt", con=cnx, index=False, if_exists="replace")
            st.success("Saved!")

    
if do.lower() == 'sort food':
    st.title("Russian Bistro")
    sort_food()
else:
    st.title("Complex Receipt Receiver")
    st.write("For when receipts are too complex to sort who got what")
    rr = receiptReceiver()