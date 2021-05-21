"""
Starts a streamlit script to allow people to select which foods they bought. For use with payme.
"""

import streamlit as st
import numpy as np
import pandas as pd
import sqlalchemy as sq

engine = sq.create_engine("sqlite:///data/food.db", connect_args={"check_same_thread":False})
cnx = engine.connect()

###################
# Users claim food
###################


class labelFood:
    def __init__(self):
        try:
            data = pd.read_sql("receipt", con=cnx)
        except:
            st.error("No receipt submitted. Have the payer add the receipt first!")
            st.stop()
        with st.beta_expander("How to"):
            st.write(
                """
            __Initial Input:__
            
            1. Select receipt
            1. Choose your name
            1. Select your order (or an order you shared)
            1. Add how many you ordered. If order was split with three people, just add your portion (ex: if 33%, enter 0.33)
            1. Review selection, hit `Confirm and Submit`
            1. Repeat for each order
            
            __Once all Meals are Claimed:__
            
            A message will show and below it in a codebox a summary of each person's orders.
            
            1. Copy the content of codebox
            1. In the sidebar click `Get venmo links`
            1. Paste into `Add name and food prices*`
            1. Click out of the box
            1. Scroll down, click copy to get your venmo links
            
            """
            )
        labels = data["name"].unique()

        selected = st.selectbox(
            "Choose a receipt!", options=labels, format_func=self.format_labels
        )
        ph_show = st.empty()

        # dictionary where keys are the food, values are a list of [price, num_ordered]
        data2 = data[data["name"] == selected] # filter to selected receipt
        food_dict, names_list = self.food_df_to_dict(data2)
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
                    "label": ["test_05-02"],
                }
            )
        show = ph_show.checkbox("Show me everyone's submission")
        if show:
            st.table(df_saved[df_saved['label']==selected])
            st.stop()
        names = self.name_chooser(df_saved, names_list)
        meals = self.meal_chooser(df_saved, food_dict)
        if not meals:
            ph_show.empty()
            # if no meals in the list, then we're done. Just show the df.
            st.success("All meals have been claimed! Copy paste the below into `Get venmo links` to get venmo links.")
            results = df_saved[df_saved['label'] == selected]
            self.results_formatter(results, data2)
            st.stop()
        name, order, amount = self.info_gather(names, meals, df_saved, food_dict, selected)
        self.ph_info = st.empty()
        self.ph_table = st.empty()

        if not amount or not order or not name:
            self.ph_info.info(
                "Step 1. Select the meal you ordered or shared, and write the amount of each. If shared, use fractions."
            )
            with self.ph_table.beta_container():
                st.write("__Your Submissions__")
                user_table = df_saved[(df_saved['label']==selected) & (df_saved['name']==name)]
                st.table(user_table)
            st.stop()

        self.ph_info.info("Step 2. Review your selection, then submit the data.")
        receipt_df = self.user_choose_meal(amount, order, name, food_dict)
        # add to db
        if st.button("Confirm and Submit"):
            self.save_to_db(receipt_df, df_saved, selected, name)

    def format_labels(self, label):
        """
        Used for the format_func paramater of st.selectbox
        """
        label_lst = label.split("_")
        new_label = f"{label_lst[0]} ({label_lst[1]})"
        return new_label

    def food_df_to_dict(self, dataframe):
        """
        Creates a dictionary out of receipt dataframe, with the "item" column as keys
        """
        my_dict = {}
        new_df = dataframe.groupby("item").sum()
        for item in new_df.index:
            my_dict[item.lower()] = [new_df.loc[item, "price"], new_df.loc[item, "amount"]]
        names_list_dirty = dataframe['people'].unique()[0].split(',')
        names_list = [name.strip() for name in names_list_dirty]
        return my_dict, names_list

    def name_chooser(self, df_saved, all_names):
        """
        Eliminates names that already occurred in the db
        """
        names = []
        # remove names and meals from options if already in db
        for name in all_names:
            if name not in list(df_saved["name"].unique()):
                names.append(name)
        names.sort()
        all_names.sort()
        return all_names

    def meal_chooser(self, df_saved, food_dict):
        """
        Eliminates meals that are in db + have been accounted for
        """
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
            elif meal.lower() in ["tip", "tax", "fees", "total", "subtotal"]:
                meals.remove(meal)

        meals.sort()
        return meals

    def info_gather(self, names, meals, df_saved, food_dict, receipt_name):
        """
        Gathers info from user
        """
        # gather user info
        name = st.selectbox("Name", options=names)
        colo, cola = st.beta_columns(2)
        with colo:
            order = st.selectbox("Select an order", options=meals)
        num_item = float(food_dict[order.lower()][1])
        receipt_df = df_saved[(df_saved['label'] == receipt_name)]
        receipt_grpd = receipt_df.groupby('food').sum()
        try:
            amt_order_recorded = receipt_grpd.loc[order,'amount']
        except:
            amt_order_recorded = 0.0
        
        with cola:
            amount = round(st.number_input(
                f"How many? (Left to claim: {round(num_item - amt_order_recorded,2)})", step=1.0, max_value=round(num_item - amt_order_recorded,2), min_value=0.0
            ),2)

        return name, order, amount

    def user_choose_meal(self, amount, order, name, food_dict):
        """
        Function that gathers user input for which meal they had
        """
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

        receipt_df["total_item_price"] = round(receipt_df["amount"] * receipt_df["price"],2)

        # calculate and present user's taxes, tips, subtotal, total
        user_subtotal = sum(receipt_df["total_item_price"])
        with self.ph_table.beta_container():
            st.write("__Your item__")
            st.table(receipt_df)

        total, subtotal, tip, tip_perc, sales_tax_perc = self.extra_calc(
            food_dict, user_subtotal
        )

        st.info(
            f"""
        * Tax was {sales_tax_perc * 100}%, tip was {round((tip/subtotal) * 100,1)}%
        * Your subtotal is ${round(user_subtotal,2)}
        * With tip and tax this meal cost ${round(total,2)}"""
        )

        return receipt_df

    def extra_calc(self, food_dict, user_subtotal):
        """
        Calculates percentages for tip and tax. Extracts subtotal from food dict.
        """
        tip = food_dict["tip"][0]
        subtotal = food_dict["subtotal"][0]
        tip_perc = tip / subtotal
        sales_tax_perc = round(food_dict["tax"][0] / subtotal, 2)
        user_total = (
            user_subtotal
            + (user_subtotal * sales_tax_perc)
            + (user_subtotal * tip_perc)
        )

        return user_total, subtotal, tip, tip_perc, sales_tax_perc

    def save_to_db(self, receipt_df, df_saved, receipt_name,name):
        """
        Allows user to submit and save to db
        """
        try:
            receipt_df["label"] = receipt_name
            df_saved = df_saved.append(receipt_df)
            df_saved.to_sql("food", cnx, if_exists="replace", index=False)
            st.success("Saved to db!")

        except:
            st.error("Couldn't save to db, tell Pete")
            
    def results_formatter(self, results, receipt_df):
        '''
        Formats the results so they can be directly copied into payme manual mode.
        '''
        results_dict = {}
        receipt_df = receipt_df.set_index('item')
        # gather info to format
        
        for i, row in results.iterrows():
            name = row['name']
            total_item_price = row['total_item_price']
            
            if name in results_dict.keys():
                results_dict[name].append(total_item_price)
            else:
                results_dict[name] = [total_item_price]
        results_dict['---DO NOT DELETE BELOW---'] = []
        results_dict['%%tax'] = [receipt_df.loc['tax','price']]
        results_dict['%%tip'] = [receipt_df.loc['tip','price']]
        results_dict['%%fees'] = [receipt_df.loc['fees','price']]
        results_dict['%%description'] = [self.format_labels(receipt_df['name'].iloc[0])]
        
        results_str = ''
        for key in results_dict.keys():
            line = f'{key}:'
            for price in results_dict[key]:
                line += f' {price}'
            results_str += f'''
{line}'''
        st.code(results_str)
        
        with st.beta_expander("See everyone's claimed meals"):
            st.table(results)


###################
# Add receipt to db
###################


class receiptReceiver:
    def __init__(self):
        """
        Class of functions to add receipt info so it can be sorted by users in the sort_food() function
        """
        try:
            r_df = pd.read_sql("receipt", cnx)
            receipt = r_df["date"] == str(dt.datetime.now().date())
            # receipt = pd.DataFrame(columns = r_df.columns)
        except:
            receipt = pd.DataFrame(columns=["food", "price", "amount", "date"])

        self.receipt = receipt
        self.add_meals()

    def add_meals(self):
        """
        Creates meals
        """
        st.info(
            """Step 1. Add meals using the format `burger: 15.81, 4`
* The first number represents how much one meal cost
* The second number represents how many times that meal was purchased"""
        )
        receipt = st.text_area("One meal info per line")

        if not receipt:
            st.stop()

        df = self.detail_meals(receipt)
        df = self.add_fees(df)
        names_lst = self.add_users()
        self.save_df(df, names_lst)

    def detail_meals(self, receipt):
        """
        Extracts costs for each meal
        """
        r_list = receipt.split("\n")
        food_lst = [food.split(":")[0].strip() for food in r_list]
        money_lst = [food.split(":")[1].strip() for food in r_list]
        price_lst = [float(food.split(",")[0].strip()) for food in money_lst]
        amount_lst = [float(food.split(",")[1].strip()) for food in money_lst]

        new_food_lst = []
        for i in range(len(food_lst)):
            food = food_lst[i]
            amt = amount_lst[i]
            new_food = f"{food} ({amt} bought)"
            new_food_lst.append(new_food)
        df = pd.DataFrame(
            {"item": new_food_lst, "price": price_lst, "amount": amount_lst}
        )
        st.table(df)
        return df

    def add_fees(self, dataframe):
        """
        Has user add taxes, fees, etc.
        """
        subtotal = sum(dataframe["price"] * dataframe["amount"])
        st.write(f"__Subtotal__ is ${round(subtotal,2)}")
        st.info("Step 2. Add fees, taxes, gratuity")

        col_tax, col_tip = st.beta_columns(2)
        with col_tax:
            tax = st.number_input("Taxes ($)", step=1.0)
        with col_tip:
            tip = st.number_input("Tip ($)", step=1.0)
        fees = st.number_input("Fee ($)", step=1.0)
        if not tip:
            st.stop()
        total = subtotal + tax + tip + fees
        st.write(f"__Total charged__ to the card is: ${round(total,2)}")

        dataframe = dataframe.append(
            pd.DataFrame(
                {
                    "item": ["tax", "tip", "fees", "subtotal", "total"],
                    "price": [tax, tip, fees, subtotal, total],
                    "amount": [0, 0, 0, 0, 0],
                }
            )
        )

        return dataframe
    
    def add_users(self):
        '''
        Asks payer to add everyone who was in the group during meal time
        '''
        st.info("Step 3. Add everyone (including yourself!) who is sharing the costs.")
        everyone_str = st.text_input("Add names, separated by a comma (Ex: Russ, Fuss, Muss)")
        if not everyone_str:
            st.stop()
        return everyone_str

    def save_df(self, dataframe, names_lst):
        """
        Saves user created info
        """
        import datetime as dt
        dataframe = dataframe.sort_values('item')
        st.info("Step 4. Tag, review, and save!")
        label = st.text_input("Give a name to the receipt")
        label = label + "_" + str(dt.datetime.now().date())[5:]        
        dataframe["name"] = label
        dataframe['people'] = str(names_lst) # sqlite does not support storing lists in cells
        st.table(dataframe)
        if not st.button("Save to Database"):
            st.stop()

        dataframe["date"] = str(dt.datetime.now().date())

        try:
            old_df = pd.read_sql("receipt", con=cnx)
            if label in old_df['name'].unique():
                label2 = label + "_new"
                dataframe['name'] = label2
            dataframe = dataframe.append(old_df)
            dataframe.to_sql("receipt", con=cnx, index=False, if_exists="replace")
        except:
            dataframe.to_sql("receipt", con=cnx, index=False, if_exists="replace")
            
        st.success("Step 5. Saved! Let everyone know it's time to claim their meals!")
