import streamlit as st
import sqlalchemy as sq
import pandas as pd
# Everything you need to mess with the dataset

def adv_settings():
    '''
    Shows an expander with option to submit data to database
    '''
    with st.beta_expander("Advanced settings"):
        st.write("Not required, but very fun")
        col_save,col_show = st.beta_columns([0.33,1])

        with col_show:
            button_show = st.button(label='Preview the Database')
        with col_save:
            button_save = st.button(label='Submit to Database')

        try:
            if button_save == True:
                ### THIS IS WHERE ITEMIZED SHOULD BE SAVED
                saveus = saveInfo(my_total, my_food, tip_perc, tax_perc, fee_part,showme='no')
                saveus.save_table()
                st.balloons()

            if button_show == True:
                showus = saveInfo()
                dataframe = showus.read_table()
                dataframe = dataframe.iloc[:,1:]
                show_me = dataframe.tail()
                st.table(show_me)
        except:
            st.info("Database function down, come back later.")
            
class getCurrency():
    def __init__(self):
        '''
        Gets the latest currency->USD conversion rates from ratesapi.io
        '''
        import datetime as dt
        if dt.datetime.now().isocalendar()[2] % 2 == 0:
            # if day of the week is even (TRSat), call currency api
            self.new_rates()
            self.rate_ctry_merge()
            
        self.get_df()
    
    def new_rates(self):
        '''
        Scrapes and returns latest currency info
        '''
        import requests
        import pandas as pd
        api = "https://api.ratesapi.io/api/latest?base=USD"
        response = requests.get(api)
        rates = response.json()
        rates_df = pd.json_normalize(rates).T.reset_index()
        rates_df.columns = ['currency','rate']
        rates_df['currency'] = rates_df['currency'].str.replace('rates.','')
        self.rates_df = rates_df
    def rate_ctry_merge(self):
        '''
        Merges, formats, and saves to db the country info with newly scraped currency rates
        '''
        import sqlalchemy as sq
        import pandas as pd
        engine = sq.create_engine("postgres://postgres:helllo@192.168.1.240:5432/payme")
        cnx = engine.connect()
        self.country_df = pd.read_sql('country_currency',cnx)
        meta = sq.MetaData()
        meta.reflect(bind=engine)
        
        df = self.rates_df
        df = df.merge(self.country_df, left_on='currency', right_on='code')
        df = df.drop_duplicates(['currency_x','currency_y','code']).reset_index(drop=True)
        df = df.rename({'currency_y':'currency'},axis=1)
        df = df.drop('currency_x',axis=1)
        # rename countries to more well-known
        df = df.replace({
            'American Samoa':'United States',
            'Bouvet Island':'Norway',
            'Cook Islands':'New Zealand',
            'Guernsey':'United Kingdom',
            'Korea, Republic of':'South Korea',
            'Liechtenstein':'Switzerland',
            'Russian Federation':'Russia',
            'Åland Islands':'European Union'
        })
        import datetime as dt
        df['date_updated'] = dt.datetime.now().date()
        df.to_sql("currency_rates",cnx, if_exists='replace', index=False)
        
    def get_df(self):
        '''
        Returns saved currency info from db
        '''
        import sqlalchemy as sq
        import pandas as pd
        engine = sq.create_engine("postgres://postgres:helllo@192.168.1.240:5432/payme")
        cnx = engine.connect()
        
        self.df = pd.read_sql("currency_rates",cnx,parse_dates='date_updated')
        
    def scrape_ctr():
        '''
        Saved for posterity. Scrapes website for country currency info
        '''
        url = "http://www.exchange-rate.com/currency-list.html"
        tables = pd.read_html(url) # scrapes table on page
        country_currency = tables[0]
        country_currency.columns = ['country','currency','code','comment']
        country_currency = country_currency.drop(0).reset_index(drop=True)
        country_currency = country_currency.drop('comment',axis=1)
        return country_currency

            
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
        engine = sq.create_engine(f'postgres://{us_pw}@{db_ip}:{port}/payme')
        cnx = engine.connect()
        meta = sq.MetaData()
        meta.reflect(bind=engine) # get metadata
        self.payme_now = meta.tables['payme_now'] # load metadata of payme_now table
        column = pd.Series(cnx.execute(sq.select([self.payme_now.c.id]))) # select ID column, load as a series
        group_id = np.random.randint(1000,6000) # create random integer for the group
        for x in range(10): # check that group_id is not alread in column
            if group_id in column:
                group_id = np.random.randint(1000,6000)

        if group_id in column:
            st.error("Group ID is already in the table, try again")
            st.stop()

        if showme=='no':

            # format data into proper list of dictionaries
            tz = timezone('US/Eastern')
            result = []

            for key in my_total.keys():
                person = {
                    'txn_id':group_id, # assign random integer
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

class dbTokenizer():
    def __init__(self, us_pw, db_ip, port):
        '''
        Initializes db for saving or loading encrypted venmo tokens, retreiving user data.
        '''
        engine = sq.create_engine(f"postgres://{us_pw}@{db_ip}:{port}/payme")
        meta = sq.MetaData()
        meta.reflect(engine)
        self.cnx = engine.connect()
        self.meta = meta
        
    def copy_names(self, my_id, username):
        '''
        Copies preapproved person's username and nicknames to the users table of db
        '''
        cnx = self.cnx
        meta = self.meta
        preapp = meta.tables['preapproved']
        users = meta.tables['users']
        username = username.lower()
        
        query = sq.select([preapp.c.nicknames]).where((preapp.c.id==my_id))
        resultset = cnx.execute(query).fetchall()
        data = resultset[0]
        
        query = sq.insert(users)
        value = {
            'id':my_id,
            'username':username,
            'nicknames':data[0]
        }
        try:
            ''
            # COMMENTED OUT TO TEST save_token
            cnx.execute(query,value)
        except Exception as e:
            if e.code == 'gkpj':
                st.sidebar.error(f"{username} already taken, try again.")
                st.stop()
            else:
                st.sidebar.error(f"Something bad happened while copying. Tell Pete about this error: {e.code}")
                st.stop()

    def save_token(self, my_id, token):
        '''
        Saves the encrypted token to the secret table of db.
        '''
        cnx = self.cnx
        meta = self.meta
        preapp = meta.tables['preapproved']
        secret = meta.tables['secret']       
        
        # grab venmo_id
        query = sq.select([preapp.c.venmo_numid]).where(preapp.c.id == my_id)
        resultset = cnx.execute(query).fetchall()
        query = sq.insert(secret)
        value = {'id':my_id,
                 'venmo_numid':int(resultset[0][0]),
                 'access_token':str(token)}
        try:
            cnx.execute(query, value)
        except Exception as e:
            if e.code == 'gkpj':
                st.sidebar.error("Whoops, you're already signed up!")
                st.stop()
            else:
                st.sidebar.error(f"Something bad happened while saving. Tell Pete about this error: {e.code}")
                st.stop()
        
    def get_token(self,my_id):
        '''
        Gets encrypted token from db.
        '''
        table = self.meta.tables['secret']
        cnx = self.cnx
        query = sq.select([table.c.access_token]).where(table.c.id==my_id)
        resultset = cnx.execute(query).fetchall()
        token = resultset[0][0]
        return token
    def get_user_name(self, username):
        '''
        Returns the first name of the user that logged in, for personalization
        and eliminating self-charge purposes.
        '''
        meta = self.meta
        cnx = self.cnx
        users = meta.tables['users']
        query = sq.select([users.c.name]).where(users.c.username == username)
        resultset = cnx.execute(query)
        name = resultset[0][0]
        return name
    def find_self(self, my_id, their_name):
        '''
        Checks whether my_name is the name of the person currently logged in
        '''
        meta = self.meta
        cnx = self.cnx
        nicks = meta.tables['nicknames']
        
        user = their_name.lower()
        query = sq.select([nicks.c.names, nicks.c.nicknames]).where(nicks.c.id == my_id)
        resultset = cnx.execute(query).fetchall()
        my_alias = pd.DataFrame(resultset)
        my_nicks = my_alias[1]
        
        if my_nicks.str.contains(user).sum() > 0:
            i_am = my_alias.iloc[0,0].title()
            return i_am
        else:
            return
    def get_user_id(self,my_name=None, username=None):
        '''
        Checks whether the user exists in a preapproved db. 
        Returns user id from names or usernames
        '''
        meta = self.meta
        cnx = self.cnx
        users = meta.tables['users']
        
        if my_name:
            name = my_name.lower()
            # check for name in nickname column
            query = sq.select([users.c.id]).where(users.c.nicknames.contains(name))
            
        if username:
            # check for matching username in username column
            name = username.lower()
            query = sq.select([users.c.id]).where(users.c.username == name)
            
        resultset = cnx.execute(query).fetchall()
        # if not there, report that the user was not found
        if not resultset:
            st.warning(f"User {name.title()} not found.")
            st.stop()
        # if there, get the userid or warn of multiple users
        else:
            if len(resultset)==1:
                user_ids = resultset[0][0]
            else:
                st.warning("Multiple possible users found")
        return user_ids
       
    def get_approved(self,verif_code):
        '''
        Finds preapproved users and gets their local_id from local db
        
        return
        ------
        local_id: int
        '''
        meta = self.meta
        cnx = self.cnx
        
        preapp = meta.tables['preapproved']

        # search for requestee in the local db
        query = sq.select([preapp.c.id]).where(preapp.c.invite_code == verif_code) 
        resultset = cnx.execute(query).fetchall()
        if not resultset:
            st.sidebar.error(f"Wrong invite code. Try again or contact Pete!")
            st.stop()
        else:
            result_list = list(resultset[0])
            if len(result_list)==1:
                user_id = int(result_list[0])
            else:
                st.error("More than one user has the same invite code. Contact Pete!")
        return user_id
    