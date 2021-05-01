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

# dictionary where keys are the food, values are a list of [price, num_ordered]
food_dict = {
    "infused shot (13)": [6, 13],
    "lavender fusion (2)": [9, 2],
    "moskow mule (1)": [9, 1],
    "eggplant appetizer (2)": [8, 2],
    "vareniki + potato and mushrooms (2)": [17, 2],
    "fresh red salmon caviar karat (1)": [35, 1],
    "blini with stuffing (salmon) (1)": [12, 1],
    "classical julienne, plain (1)": [14, 1],
    "russian pelmeni + beef and pork (1)": [18, 1],
    "chicken tabaka (1)": [21, 1],
    "tandoori large plate (1)": [69.99, 1],
    "martini infused + apple and cinnamon (1)": [12, 1],
    "dessert (6)": [round(42 / 6, 2), 6],
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


all_names = ["Peter", "Matt", "Steve", "Aron", "Julie", "Grace", "Russell"]
# theres a bug where removing the name from names when names is the iteree,
# 
names = []
# remove names and meals from options if already in db
for name in all_names:
    if name not in list(df_saved["name"].unique()):
        names.append(name)
names.sort()

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
# gather user info
name = st.selectbox("Name", options=names)
order = st.multiselect("What did you order?", options=meals)
amount_str = st.text_input("How much? (Ex: 1, 2, 0.5)")

ph = st.empty()

if not amount_str or not order or not name:
    st.info(
        "Select all the foods you ordered or shared, and write the amount of each. If shared, use fractions."
    )
    with ph.beta_container():
        st.write("__Current Database__")
        st.table(df_saved)
    st.stop()

# format inputs
amount_list = amount_str.split(",")
amount_list = [float(x.strip()) for x in amount_list]
price = [food_dict[x.lower()][0] for x in order]

# store inputs
receipt_dict = {}
for i in range(len(order)):
    food = order[i]
    amount = amount_list[i]
    receipt_dict[food] = [amount]

# prettify inputs for user's benefit

receipt_df = pd.DataFrame(
    {
        "name": [name for i in range(len(receipt_dict.keys()))],
        "food": receipt_dict.keys(),
        "price": [food_dict[food.lower()][0] for food in receipt_dict.keys()],
        "amount": [receipt_dict[food][0] for food in receipt_dict.keys()],
    }
)

receipt_df["total_item_price"] = receipt_df["amount"] * receipt_df["price"]

# calculate and present user's taxes, tips, subtotal, total
user_subtotal = sum(receipt_df["total_item_price"])
with ph.beta_container():
    st.write("Your items")
    st.table(receipt_df)

total = user_subtotal + (user_subtotal * sales_tax_perc) + (user_subtotal * tip_perc)
st.info(
    f"""
* Tax was {sales_tax_perc * 100}%, tip was {round((tip/subtotal) * 100,1)}%
* Your subtotal is ${user_subtotal}
* Your total is ${round(total,2)}"""
)

# add to db
if st.button("Confirm and Submit"):
    try:
        df_saved = df_saved.append(receipt_df)
        with ph.beta_container():
            st.write("New Database")
            st.table(df_saved)
        df_saved.to_sql("food", cnx, if_exists="replace", index=False)
        st.success("Saved to db!")
    except:
        st.error("Couldn't save to db, tell Pete")
