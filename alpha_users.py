import streamlit as st
import sqlalchemy as sq
import pandas as pd
import numpy as np

#######################
### Database Region ###
#######################

####### import from secret file
access_code_link = "https://api.venmo.com/v1/oauth/authorize?client_id=1112&scope=access_profile,make_payments&response_type=code"

class dbTokenizer():
    def __init__(self, us_pw, db_ip, port):
        '''
        Initializes db for saving or loading encrypted venmo tokens.
        '''
        engine = sq.create_engine(f"postgres://{us_pw}@{db_ip}:{port}/payme")
        self.cnx = engine.connect()
        meta = sq.MetaData()
        meta.reflect(engine)

        self.table = meta.tables['secret']
        
    def save_token(self, my_id, token):
        '''
        Saves the encrypted token to db.
        '''
        cnx = self.cnx
        table = self.table
        query = sq.insert(table)
        value = {'id':my_id,'token':token}
        cnx.execute(query, value)

    def get_token(self,my_id):
        '''
        Gets encrypted token from db.
        '''
        table = self.table
        cnx = self.cnx
        query = sq.select([table]).where(table.c.id==my_id)
        resultset = cnx.execute(query).fetchall()
        df = pd.DataFrame(resultset)
        df.columns = resultset[0].keys()
        df = df.set_index('id')
        token = df.loc[my_id,'token']
        return token
        

#########################
### Encryption Region ###
#########################

# SOURCE: https://stackoverflow.com/questions/2490334/simple-way-to-encode-a-string-according-to-a-password/55147077#55147077

import secrets
from base64 import urlsafe_b64encode as b64e, urlsafe_b64decode as b64d

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

backend = default_backend()
iterations = 100_000

def _derive_key(password: bytes, salt: bytes, iterations: int = iterations) -> bytes:
    """Derive a secret key from a given password and salt"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt,
        iterations=iterations, backend=backend)
    return b64e(kdf.derive(password))

def password_encrypt(message: bytes, password: str, iterations: int = iterations) -> bytes:
    salt = secrets.token_bytes(16)
    key = _derive_key(password.encode(), salt, iterations)
    return b64e(
        b'%b%b%b' % (
            salt,
            iterations.to_bytes(4, 'big'),
            b64d(Fernet(key).encrypt(message)),
        ))

def password_decrypt(token: bytes, password: str) -> bytes:
    decoded = b64d(token)
    salt, iter, token = decoded[:16], decoded[16:20], b64e(decoded[20:])
    iterations = int.from_bytes(iter, 'big')
    key = _derive_key(password.encode(), salt, iterations)
    try:
        token = Fernet(key).decrypt(token)
        return token
    except:
        st.error("Password is incorrect, unable to decrypt token")
        st.stop()

def create_token(us_pw, db_ip, port):
    '''
    Streamlit frontend.
    Uses the encrypt function create an encrypted token. Returns token + user submitted pw.
    '''
    # Explain to user
    with st.beta_expander("Click me for more info"):
        st.write("""
        * Your __password__ will not be saved. Instead, it is used along with Fernet encryption to create a personalized encryption key.
        * Your __access token__ is saved in encrypted form with the use of your personalized encryption key. This app cannot access your token without the personalized password.
        * Since the password is never saved, it must be entered on each use.""")
        
    user = st.sidebar.text_input("Who are you?")
    pw = st.sidebar.text_input("Create a Password", type="password")
    token = st.sidebar.text_input("Access Token", type="password")
    st.sidebar.info(f"Get your access token by clicking [here]({access_code_link})")
    
    if st.sidebar.button('Submit'):
        token_enc = password_encrypt(token.encode(), pw)
        token = dbTokenizer(us_pw, db_ip, port)
        token.save_token(my_id, token_enc.decode())
        st.success("Submitted! Remember your password, because we won't.")
        st.info("Login to continue!")
        st.stop()
        # not returning anything to force user to login

def get_user_id(my_name, us_pw, db_ip, port):
    '''
    get user id from names
    '''
    import sqlalchemy as sq
    engine = sq.create_engine(f"postgres://{us_pw}@{db_ip}:{port}/payme")
    cnx = engine.connect()
    meta = sq.MetaData()
    meta.reflect(engine)
    users = meta.tables['users']   

    name = my_name.lower()
    query = sq.select([users.c.id]).where(users.c.name.contains(my_name))
    resultset = cnx.execute(query).fetchall()
    if not resultset:
        query = sq.select([users.c.id]).where(users.c.nicknames.contains(my_name))
        resultset = cnx.execute(query).fetchall()
    if not resultset:
        st.warning(f"User {my_name} not found.")
        st.stop()
    else:
        if len(resultset)==1:
            user_ids = resultset[0][0]
        else:
            st.warning("Multiple possible users found")
    return user_ids

def get_secrets(my_name, us_pw, db_ip, port):
    '''
    Get local_id and venmo_numid from local db
    '''
    import sqlalchemy as sq
    engine = sq.create_engine(f"postgres://{us_pw}@{db_ip}:{port}/payme")
    cnx = engine.connect()
    meta = sq.MetaData()
    meta.reflect(engine)
    temp = meta.tables['temp']
    
    name = my_name.lower()
    query = sq.select([temp.c.id, temp.c.venmo_numid]).where(temp.c.name.contains(name)) 
    resultset = cnx.execute(query).fetchall()
    if not resultset:
        query = sq.select([temp.c.id, temp.c.venmo_numid]).where(temp.c.nicknames.contains(name))
        resultset = cnx.execute(query).fetchall()
        
    result_list = list(resultset[0])
    if not resultset:
        st.warning(f"User {my_name} not found.")
        st.stop()
    else:
        if len(result_list)==2:
            user_id = result_list[0]
            venmo_id = result_list[1]
        else:
            st.warning("Multiple possible users found")
    return user_id, venmo_id
def get_access_token(us_pw, db_ip, port):
    '''
    Prompts for info to initiate get_user_id and db_tokenizer functions
    Grabs access token of selected user from db
    '''
    coln,colpw = st.beta_columns(2)
    with coln:
        name = st.sidebar.text_input("Enter name*")
        name = name.lower()
    with colpw:
        pw = st.sidebar.text_input("Enter password*", type="password")
        
    if name and pw:
        my_id = get_user_id(name, us_pw, db_ip, port)
    
        token = dbTokenizer(us_pw, db_ip, port) # initialize db cnx
        token = token.get_token(my_id) # get token using id
        access_token = password_decrypt(token.encode(), pw).decode()
        return access_token, name
    else:
        st.stop()

########################
### Venmo API Region ###
########################
from venmo_api import Client
import venmo_api

class venmoThings():
    def __init__(self, access_token):
        '''
        Connects to venmo to request money.
        '''
        self.venmo = Client(access_token)
        self.txn = self.venmo.payment
        
    def search_for_user(self,user_str):
        '''
        Returns user_id, needed for transactions. Asks for confirmation before returning the user_id.

        input
        -----
        user_str: str
            Username or name to search for
        '''
        venmo = self.venmo
        users = venmo.user.search_for_users(user_str)        
        if users:
            for i in range(10):
                text = st.write(f"Were you looking for '{users[i].first_name} {users[i].last_name}', username '{users[i].username}'? (y/n)")
                if text == 'y':
                    self.my_id = users[0].id
                    return
                else:
                    pass
        else:
            return "No match found"
        
    def request(self, amount, message, target_user_id):
        '''
        Request user some amount
        
        input
        -----
        amount: float
            Money to request
        message: str
            Not attach to request
        '''
        if target_user_id:
            self.txn.request_money(amount = amount, note = message, target_user_id = target_user_id)
        else:
            st.error("Must find user id first")
        
    def send(self, amount, message):
        '''
        Pay user some amount
        
        input
        -----
        amount: float
            Money to pay
        message: str
            Not attach to payment
        '''
        self.txn.send_money(amount = amount, note = message, target_user_id = self.my_id)

        
#######################
### Main App Region ###
#######################

def format_names(my_str):
    'for use with format_fun arg, capitalizes string'
    return my_str.capitalize()

def format_lists(my_list):
    '''formats list to string'''
    new_str = str(my_list)
    new_str = new_str.replace("'"," ")
    new_str = new_str.replace("[","")
    new_str = new_str.replace("]","")
    new_str = new_str.replace(", "," \n")
    new_str = new_str.title()
    return new_str

def paramtext_formatter(messages):
    '''
    Formats the link_output messages from payme.py to be human-readable
    
    input
    -----
    messages: dict
        Dictionary of name:message, where the message is url compatible formatted
    '''
    neat_messages = {}
    for name, mess in messages.items():
        message = mess.replace('%20', ' ') # whitespace
        message = message.replace('%0A', ' ') # newline (removed)
        message = message.replace('%25','%') # percent sign
        message = message.replace('%3C','<') # less than sign
        neat_messages[name] = message
    return neat_messages

def app(my_dic, total, tax, tip, misc_fees, messages, db_info):
    us_pw, db_ip, port = db_info[0],db_info[1],db_info[2]
    st.write('# Venmo Login Alpha')
    st.warning("Currently in alpha, testing automated venmo requests")
    choice = st.sidebar.selectbox("Hello, please login!",["Login","Create token"])
    if choice == "Login":
        token, name = get_access_token(us_pw, db_ip, port)
        venmo = venmoThings(token)
        st.sidebar.success("Success! Access token found, decrypted, and verified with Venmo.")
    else:
        create_token(us_pw, db_ip, port)
        st.stop()
           
    neat_messages = paramtext_formatter(messages)
    request_dict = {}
    for person, to_request in my_dic.items():
        if person.lower() == name.lower(): # this is the requester
            my_total = to_request[0]
        else:
            amount = to_request[0]
            message = neat_messages[person]
            request_dict[person] = (amount, message)
    st.info(f"Hi {name.title()}, we can now auto request ${round(total-my_total,2)} from your friends. Your portion was ${my_total}.")
    
    st.write("## Confirm Requests")
    st.write("Double check everything, then submit when ready.")
    edit = st.checkbox("Let me edit the message")
    if edit:
        st.warning("Too bad, not going to happen.")
        st.stop()
    
    friends = []
    monies = []
    messages = []
    for person, data in request_dict.items():
        friends.append(person)
        monies.append(data[0])
        messages.append(data[1])
        
    confirm_df = pd.DataFrame({
        'person':friends,
        'amount':monies,
        'message':messages
    })
    st.table(confirm_df.set_index('person'))
    num_ppl = len(request_dict.keys())
    progress = st.progress(0)
    good = st.button('Request them!')
    if good:
        i = 0
        for person in request_dict.keys():
            my_id, venmo_id = get_secrets(person.lower(), us_pw, db_ip, port)
            venmo.request(amount = request_dict[person][0], message = request_dict[person][1], target_user_id = venmo_id)
            progress.progress((i+1/num_ppl))
            i+=1/num_ppl
        st.balloons()
        st.success("Money requested!")
            