import streamlit as st
# archive from trying to make one-click copy to clipboard a reality

def set_params(my_dic, total, tax, tip, misc_fees, view, share=False):
    'Adds parameters to url'
    st.experimental_set_query_params(
        ppl=[my_dic],
        total=total,
        tax=tax,
        tip=tip,
        misc_fees=misc_fees,
        view=view,
        share=share
    )
    
def use_params():
    '''
    Extracts and returns all parameters from the url
    '''
    info_dict = st.experimental_get_query_params()
    st.write(info_dict)
    param_receipt = info_dict['ppl'][0].replace("{","")
    param_receipt = param_receipt.replace("}","")
    param_receipt = param_receipt.replace("'","")
    
    receipt_input = param_receipt
    fees_input = float(info_dict['misc_fees'][0])
    tax_input = float(info_dict['tax'][0])
    tip_input = float(info_dict['tip'][0])
    select_input = info_dict['view'][0]
    share = bool(info_dict['share'][0])
   
    return_us = [tax_input,fees_input,tip_input,share]
    return return_us

def read_from_clipboard():
    import streamlit as st
    from bokeh.models.widgets import Button
    from bokeh.models import CustomJS
    from streamlit_bokeh_events import streamlit_bokeh_events
    from io import StringIO
    import pandas as pd


    copy_button = Button(label="Get Clipboard Data")
    copy_button.js_on_event("button_click", CustomJS(code="""
        navigator.clipboard.readText().then(text => document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: text})))
        """))
    result = streamlit_bokeh_events(
        copy_button,
        events="GET_TEXT",
        key="get_text",
        refresh_on_update=False,
        override_height=75,
        debounce_time=0)

    if result:
        if "GET_TEXT" in result:
            df = pd.read_csv(StringIO(result.get("GET_TEXT")))
            st.table(df)
    
def copy_to_clipboard(text):
    import streamlit as st
    from bokeh.models.widgets import Button
    from bokeh.models import CustomJS
    from streamlit_bokeh_events import streamlit_bokeh_events
    from io import StringIO
    import pandas as pd
    
    copy_button = Button(label="Copy All of Me")
    
    html_code = f"""<!-- The text field -->
    <input type="text" value="{text.replace(" ","%20")}" id="myInput">

    <!-- The button used to copy the text -->
    <button onclick="myFunction()">Copy text</button>"""
    
    js_code = """function myFunction() {
    /* Get the text field */
    var copyText = document.getElementById("myInput");

    /* Select the text field */
    copyText.select();
    copyText.setSelectionRange(0, 99999); /* For mobile devices */

    /* Copy the text inside the text field */
    document.execCommand("copy");

    /* Alert the copied text */
    alert("Copied the text: " + copyText.value);
    }"""
    st.write(html_code, unsafe_allow_html=True )
    copy_button.js_on_event("button_click", CustomJS(code=js_code))
    
def tg_formatter(link_output):
    '''
    Gets tg usernames from json, makes a tg link that sends all venmo requests to tg
    
    input
    -----
    link_output: dict
        Dictionary of name: venmo link, from venmo_request() function
    '''
    message = ''
   
    df_tg = pd.read_json('tg_info.json')
    df_tg['first_name'] = df_tg['first_name'].str.lower()
    
    user_dict = {}
    for i, row in df_tg.iterrows():
        for name in link_output.keys():
            lname = name.lower()
            if lname in row['first_name']:
                user = df_tg.loc[i,'username']
                user_dict[name] = link_output[name].replace(f"recipients={name}",f"recipients={user}")
                
    for name in user_dict.keys():
        venmo_req = user_dict[name]
        tg_message = f"__{name}__:%0A{venmo_req}%0A%0A"
        message += tg_message   
    
   
    ### Copy to clipboard, for easy pasting to tg ###
    
    # tg_open = f'tg://msg?text={message}'.replace(" ","%20")
    # st.write(f'<a href="{tg_open}" target="_blank" rel="noopener noreferrer">Click me for TG</a>',unsafe_allow_html=True)