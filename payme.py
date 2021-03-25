# core app. Redirects to appropriate apps.

# libraries
import streamlit as st

# files
from apps import calculator as calc
from apps import manual_mode as mm

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
<script src="https://cdn.jsdelivr.net/npm/darkmode-js@1.5.7/lib/darkmode-js.min.js"></script>
<script>
  function addDarkmodeWidget() {
    new Darkmode().showWidget();
  }
  window.addEventListener('load', addDarkmodeWidget);
</script>

"""
st.set_page_config(page_title = 'Venmo Calculator')
st.markdown(hide_streamlit_style, unsafe_allow_html=True) # hides the hamburger menu

def start():
    '''
    Thalamus. Creates the GUI and redirects requests to the appropriate scripts. The Thalamus.
    '''
    select_input = 'release' # disabled user section of payme ('alpha' to activate)
    service_chosen = st.select_slider("",options=['Delivery App','Manual Mode'])
    
    if 'Manual' not in service_chosen:
        gui = 'doordelivery'
        user_output = mm.manual_input(gui)
    else:
        gui = 'Manual'
        user_output = mm.manual_input(gui)
        
    total_input, data = calc.total_calculator(**user_output)
    # dictionary of kwargs for venmo_calc()
    user_modified = {
        'tax':user_output['tax_input'],
        'tip':user_output['tip_input'],
        'misc_fees':user_output['fees_input'],
        'description':user_output['description'],
        'total':total_input,
        'discount':user_output['discount'],
        'contribution':user_output['contribution'],
        'my_dic':data
    }
    try:
        calc_message = calc.venmo_calc(**user_modified, clean=False)
        mm.html_table(calc_message["messages"], calc_message["request_money"])

    except ZeroDivisionError:
        st.info("See the how to for more information!")
        calc_message={'request_money':None}
        st.stop()

    if st.button("Ping Pete some love!"):
        st.balloons()
        st.success("Thanks for using payme! <3")
        send_webhook() # notify Pete that someone used payme!
        st.stop()

def send_webhook():
    '''
    Sends a hook to zapier, which emails me. For the "Send Pete some love" button.
    '''
    import json
    import requests
    from apps import secret
    
    webhook_url = secret.app()
    response = requests.get(webhook_url)
    
    if response.status_code != 200:
        raise ValueError(
        'Request to zapier returned an error %s, the response is:\n%s'
        % (response.status_code, response.text)
    )
        
def app():
    '''
    Only purpose is to start the app from bash script. Own function so the rest of the functions can be organized in a logical way.
    '''
    start()

app()