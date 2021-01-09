import streamlit as st
import sqlalchemy as sq
import pandas as pd
import numpy as np

#######################
### Main App Region ###
#######################

def app(my_dic, total, messages, db_info):
    from apps import db_tool
    us_pw, db_ip, port = db_info[0],db_info[1],db_info[2]
    st.sidebar.warning("Contact Pete to opt in.")
    choice = st.sidebar.selectbox("Hello, please login!",["Login","Create token"])
    if choice == "Login":
        token, username, user_id = login_user(us_pw, db_ip, port)
        venmo = venmoThings(token)
        st.sidebar.success("Success! Access token found, decrypted, and verified with Venmo.")
    else:
        create_user(us_pw, db_ip, port)
        st.stop()
        
    tokenizer = db_tool.dbTokenizer(us_pw, db_ip, port)
    neat_messages = paramtext_formatter(messages)
    request_dict = {}
    for person, to_request in my_dic.items():
        finding = tokenizer.find_self(user_id, person)
        if finding: # this is the requester
            my_total = to_request[0]
            my_name = finding
        else:
            amount = to_request[0]
            message = neat_messages[person]
            request_dict[person] = (amount, message)
    st.info(f"Hi {my_name}, we can now auto request ${round(total-my_total,2)} from your friends. Your portion was ${my_total}.")
    
    st.write("## Confirm Requests")
    st.write("Double check everything, then submit when ready.")
    edit = st.checkbox("Let me edit the message")
    if edit:
        st.warning("Too bad, not going to happen.")
        st.stop()
    # Show a table of people to request plus messages that will be sent
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
        # Request the people!
        for person in request_dict.keys():
            # Get local id and venmo id
            my_id, venmo_id = db_tool.get_secrets(person.lower(), us_pw, db_ip, port)
            venmo.request(amount = request_dict[person][0], message = request_dict[person][1], target_user_id = venmo_id)
            progress.progress((i+1/num_ppl))
            i+=1/num_ppl
        st.balloons()
        st.success("Money requested!")
            

#######################
### Database Region ###
#######################

# access_code_link = "https://api.venmo.com/v1/oauth/authorize?client_id=1&scope=access_profile,make_payments&response_type=code"

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
    "Encrypts message using a password"
    salt = secrets.token_bytes(16)
    key = _derive_key(password.encode(), salt, iterations)
    return b64e(
        b'%b%b%b' % (
            salt,
            iterations.to_bytes(4, 'big'),
            b64d(Fernet(key).encrypt(message)),
        ))

def password_decrypt(token: bytes, password: str) -> bytes:
    "Decripts message given the correct password"
    decoded = b64d(token)
    salt, iter, token = decoded[:16], decoded[16:20], b64e(decoded[20:])
    iterations = int.from_bytes(iter, 'big')
    key = _derive_key(password.encode(), salt, iterations)
    try:
        token = Fernet(key).decrypt(token)
        return token
    except:
        st.sidebar.error("Incorrect password")
        st.stop()

        
from contextlib import contextmanager, redirect_stdout
from io import StringIO
from time import sleep

@contextmanager
def st_capture(output_func):
    '''
    Captures printout statements, pushes them to streamlit frontend. 
    '''
    with StringIO() as stdout, redirect_stdout(stdout):
        old_write = stdout.write

        def new_write(string):
            ret = old_write(string)
            output_func(stdout.getvalue())
            return ret
        
        stdout.write = new_write
        yield
        
def create_user(us_pw, db_ip, port):
    '''
    Streamlit frontend.
    Uses the encrypt function to create an encrypted token. Returns token + user submitted pw.
    '''
    # Explain to user
    from apps import db_tool
    with st.sidebar.beta_expander("Click me for more info"):
        st.write("""
        * Your __password__ will not be saved. Instead, it is salted and used with Fernet encryption to create a personalized encryption key.
        * Your __access token__ is saved in encrypted form with the use of your personalized encryption key. This app cannot access your token without the personalized password.
        * Since the password is never saved, it must be entered on each use.""")
        
    # grab essential information
    user = st.sidebar.text_input("Create a username*")
    verif = st.sidebar.text_input("Enter invite code*", type="password")
    if verif:
        tokenizer = db_tool.dbTokenizer(us_pw, db_ip, port)
        my_id = tokenizer.get_approved(verif)
    pw = st.sidebar.text_input("Create a password*", type="password")
    
    #### This is fishy af, removed ####
    # token = st.sidebar.text_input("Paste venmo access token*", type="password")
    # st.sidebar.info(f"Get your access token by clicking [here]({access_code_link})")
    
    venmo_user = st.sidebar.text_input("Enter venmo username, phone number, or email")
    venmo_pw = st.sidebar.text_input("Enter venmo password", type = "password")
    
    output = st.empty()
    
    with st_capture(output.code):
        if venmo_user and venmo_pw:
            # NOTE: /.conda/envs/testing/lib/python3.8/site-packages/venmo_api/apis/auth_api.py 
            # was modified in very last function. input ---> st.sidebar.text_input
            access_code = Client.get_access_token(username=venmo_user, password=venmo_pw) # get user id from user/pw
            st.info("""To logout from Venmo, click logout in the sidebar. \n
Your access token will be stored encrypted. The only way to decrypt it is with your payme password, which is not stored.""")

            ids_output = st.sidebar.text_area("Paste the `device-id` line here")
            if ids_output: # get device-id to avoid 2fs next time
                import re
                try:
                    device_id = re.findall("device-id: *(\S+?)[ \n]",ids_output)
                    st.write(device_id)
                except:
                    st.warning("Is this the right line?")
                    st.write(f"`{device_id}`")
                    st.stop()
                
    if st.sidebar.button('Submit'):
        # encrypt token
        token_enc = password_encrypt(access_code.encode(), pw)
        device_id_enc = password_encrypt(device_id.encode(), pw)
                
        tokenizer.copy_names(my_id, user)
        tokenizer.save_token(my_id, token_enc.decode(), device_id_enc.decode())

        
        st.success("Submitted! Remember your payme password, because we won't.")
        st.info("Your Venmo user/password was not stored, however an access code was stored.")
        st.info("Login to continue!")
        st.stop()
        # not returning anything to force user to login

def login_user(us_pw, db_ip, port):
    '''
    Prompts for info to initiate get_user_id and db_tokenizer functions
    Grabs access token of selected user from db
    '''
    from apps import db_tool
    username = st.sidebar.text_input("Enter username*")
    username = username.lower()
    pw = st.sidebar.text_input("Enter password*", type="password")
    
    if username and pw:   
        token = db_tool.dbTokenizer(us_pw, db_ip, port) # initialize db cnx
        user_id = token.get_user_id(username=username)
        token = token.get_token(user_id) # get token using id
        access_token = password_decrypt(token.encode(), pw).decode()
        return access_token, username, user_id
    else:
        st.stop()

########################
### Venmo API Region ###
########################
from venmo_api import Client
import venmo_api

class venmoThings():
    def __init__(self, vuser,vpass):
        '''
        Connects to venmo to request money.
        '''
        access_token = Client.get_access_token(username=vuser, password=vpass)
        try:
            self.venmo = Client(access_token) # initialize venmo api
        except Exception as e:
            if '401' in e.msg:
                st.error("The access token is incorrect or revoked. Please contact Peter.")
                st.stop()
            else:
                st.write(vars(e))
        self.txn = self.venmo.payment # initialize venmo payment api
        
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
        
##########################
### Helper Fctn Region ###
##########################

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