import streamlit as st
import pandas as pd

# GUI for manual input option
def manual_input(gui, params):
    '''
    Manual input of costs, fees, tax, tips.
    '''
    if params:
        total_inputp, datap, tax_inputp, fees_inputp, tip_inputp, sharep = params
        
    else:
        total_inputp=0.0
        datap=''
        tax_inputp=0.0
        fees_inputp=0.0
        tip_inputp=0.0
        sharep=False
    st.title(f'Venmo Requests Calculator {gui}')
    if gui.lower() == '(alpha)':
        st.write("Let us request your friends for you!")
    else:
        st.write("Give us some info, we'll give you a personalized link!")
    with st.beta_expander(label='How To'):
        st.write(f"""
            1. Input the name and itemized money spent in a format of:
                ```
                Peter: 20.21,5.23, 3.21
                Russell: 11.01, 15.89, 1.99
                ```
                Or on a single line:
                ```
                Peter 20.21 5.23 3.21 Russell 11.01 15.89 1.99
                ```
                Or with a split cost (Peter and Russell pay 8 each)
                ```
                Peter and Russell 16
                Peter: 20.21, 5.23
                Russell 11.01 15.89 1.99
                ```
            2. Input the rest of the fees or tips as needed""")

    receipt_input = st.text_area(label="Add name and food prices*", value=datap)
    col1, col2, col3 = st.beta_columns(3)

    with col1:
        fees_input = st.number_input("Fees in dollars",step=1.0, value=fees_inputp)
    with col2:
        tax_input = st.number_input("Tax in dollars",step=1.0, value=tax_inputp)
    with col3:
        tip_input = st.number_input("Tip in dollars",step=5.0, value=tip_inputp)
    return receipt_input ,fees_input, tax_input, tip_input

def html_table(link_output, request_money):
    '''
    Presents name, amount, and custom venmo link in a sweet ass-table
    ASCII table source: http://www.asciitable.com/
    Use Hx column, add a % before it
    '''
    html_table_header = '''
    <table class="tg">
    '''
    html_table_end = '''</tr>
    </tbody>
    </table>'''
    
    html_table_data = f'''
<tbody>'''
    
    venmo_logo = 'https://raw.githubusercontent.com/pomkos/payme/main/images/venmo_logo_blue.png'
    for key in link_output.keys():
        # append each person's rows to html table 
        html_row = f'''
<tr>
    <td class="tg-0pky">{key}<br></td>
    <td class="tg-0pky">${request_money[key][0]}</td>
    <td class="tg-0pky"><a href="{link_output[key]}" target="_blank" rel="noopener noreferrer"><img src="{venmo_logo}" width="60" ></a><br></td>
</tr>'''
        html_table_data += html_row

    html_table = html_table_header + html_table_data + html_table_end
    
    st.write(html_table, unsafe_allow_html=True)
    st.write('')