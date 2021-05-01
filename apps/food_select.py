"""
Starts a streamlit script to allow people to select which foods they bought. For use with payme.
"""

import streamlit as st
import numpy as np
import pandas as pd
import sqlalchemy as sq

st.title("Russian Bistro")
engine = sq.create_engine("sqlite:///data/food.db")
cnx = engine.connect()

with st.beta_expander("How to"):
    st.write("""
    1. Choose name
    1. Choose a food item
    1. Enter how many of that meal you had.
    1. Use fractions to indicate shared orders. 0.33 if split by three, 0.5 if split by two, etc.
    1. Click `Calculate`. If everything looks good click `Confirm and Submit`
    """)

# dictionary where keys are the food, values are a list of [price, num_ordered]
food_dict = {
    "drink: infused shot (13)": [6, 13],
    "drink: lavender fusion (2)": [9, 2],
    "drink: moskow mule (1)": [9, 1],
    "meal: eggplant appetizer (2)": [8, 2],
    "meal: vareniki + potato and mushrooms (2)": [17, 2],
    "meal: fresh red salmon caviar karat (1)": [35, 1],
    "meal: blini with stuffing (salmon) (1)": [12, 1],
    "meal: classical julienne, plain (1)": [14, 1],
    "meal: russian pelmeni + beef and pork (1)": [18, 1],
    "meal: chicken tabaka (1)": [21, 1],
    "meal: tandoori large plate (1)": [69.99, 1],
    "drink: martini infused + apple and cinnamon (1)": [12, 1],
    "dessert: halva (4)": [4.5, 4],
    "dessert: kiev cake (1)": [8, 1],
    "dessert: napoleon cake (1)": [1,1],
    "dessert: medovik cake (1)": [1,1]
}

subtotal = 378.99
mb_sales_tax = 9.65
sales_tax_perc = 0.0825
sales_tax = 20.46
tip = 81.82
tip_perc = tip / subtotal
total = 490.92

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

def name_chooser():
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

def meal_chooser():
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

def info_gather(names, meals):
    '''
    Gathers info from user
    '''
    # gather user info
    name = st.selectbox("Name", options=names)
    colo, cola = st.beta_columns(2)
    with colo:
        order = st.selectbox("Select an order", options=meals)
    num_item = food_dict[order.lower()][1]
    with cola:
        amount = st.number_input("How much? (Ex: 1, 2, 0.5)", step=1.0, max_value=num_item)
    
    return name, order, amount

names = name_chooser()
meals = meal_chooser()

name, order, amount = info_gather(names, meals)
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
