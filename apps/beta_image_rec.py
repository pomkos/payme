# GUI for receipt upload option
import streamlit as st

@st.cache
def ocr_image(my_receipt='pdf'):
    '''
    Use OCR to extract information from an image. When DoorDash groups is used.
    '''
    import pytesseract as tes
    from PIL import Image
    import pandas as pd
    # process the image
    if my_receipt == 'pdf':
        text_str = tes.image_to_string('temp/page.jpg')
    else:
        text_str = tes.image_to_string(Image.open(my_receipt))
    
    return text_str.lower()

def ocr_pdf(my_receipt):
    '''
    Use OCR to extract information from an image. When DoorDash groups is used.
    '''
    from pdf2image import convert_from_bytes
    
    # process the image
    pages = convert_from_bytes(my_receipt.read(),dpi=500,fmt='png')
    i=0
    for page in pages:
        page.save(f"temp/page{i}.jpg",'JPEG')
        i+=1
    
def auto_input(gui):
    '''
    Main auto function, decides pdf vs image then organize extracted info
    '''
    from PIL import Image
    import magic
    st.title(f'Venmo Requests Calculator {gui}')
    st.write("We scan your DoorDash receipt, you get prefilled venmo links. Simple!")
    with st.beta_expander("How To"):
        st.warning("Make sure everything from 'Group Order' downwards is visible.")
        st.write("""
        1. Take a screenshot of the venmo receipt, like the sample shown below.
        2. Save the screenshot to your desktop, then drag and drop.
        3. Enter names as they appear on the receipt.
        4. Done!
        """)
        st.image('images/sample_receipt.jpg',caption='Sample receipt',width=150)
        st.info("To see your image and our extraction, click OCR feedback")
    my_receipt = st.file_uploader("Upload a screenshot or receipt",type=['png','jpg','jpeg','pdf'])
    if not my_receipt:
        st.info("Upload a screenshot of the full DoorDash receipt!")
        st.stop()
    file_type = magic.from_buffer(my_receipt.read(2048)) # get the file type

    if "pdf" in file_type.lower():
        ocr_pdf(my_receipt)
        text_str = ocr_image(my_receipt='pdf')
        st.warning("BETA. Prices not labeled correctly. Upload a screenshot instead!")
    else:
        text_str = ocr_image(my_receipt=my_receipt)

    with st.beta_expander(label="Click me for OCR feedback"):
        col_img, col_extract = st.beta_columns(2)
        with col_img:
            st.success("Uploaded!")
            try:
                if "pdf" in file_type.lower():
                    st.image('temp/page.jpg',width=250)
                else:
                    st.image(Image.open(my_receipt),width=250)
            except:
                st.warning("Can't show image")
    
    extracted = {}
    #### Get names ###
    import re

    try:
        parts = re.findall(r'(\d\d?) participants',text_str)[0]
        num_item = re.findall(r'(\d\d?) items', text_str)[0]
        extracted['participants'] = int(parts)
        extracted['items'] = int(num_item)
    except Exception as e:
        st.error("Sorry, only DoorDash receipts are supported for now.")
        st.stop()
    
    my_names = st.text_input("Write names below, separated by a comma. Ex: peter, Russell")
    if not my_names:
        st.info(f"""Add all __{extracted['participants']} names__, separated by a comma, in the order that they appear on the receipt.""")
        st.info(f"Click 'OCR feedback' to see your uploaded image")
        st.stop()
    my_names_check = my_names.split(',')
    if len(my_names_check)!=extracted['participants']:
        # if user didn't provide the right number of names, script won't work
        st.warning(f"I detected __{extracted['participants']}__ people on this receipt, but you provided __{len(my_names_check)}__ names")
        st.stop()
        
    ### Parse info ###
    # Get the names, adds additional variables like total, tip, fees, etc
    from apps import doordash as dd
    names, only_names = dd.name_maker(my_names, text_str)
    # Assign prices to each variable, eliminate extras
    names_prices = dd.receipt_formatter(text_str, names, only_names, ocr=True)
    # Confirm with user total is correct
    sane = dd.sanity_check(names_prices)
    if sane == False:
        st.stop()
    # standardize output for rest of script    
    return_me = dd.receipt_for_machine(names_prices, description='', only_names = only_names)
    return return_me

def extracted_col(extracted,all_money,not_people,receipt_input,names, status = 'good'):
    '''
    Presents extracted information to the user in a column under the "ocr feedback" expander
    '''
    import pandas as pd
    # present info
    combed_df = pd.DataFrame({
        "category":['num people', 'items'],
        "data":[extracted['participants'], extracted['items']]
    })
    # Append names
    for name in names:
        try:
            plural = ['s' if extracted[name]>1 else '']
            name_df = pd.DataFrame({
                "category":name,
                "data":[f'bought {extracted[name]} item{plural[0]}']})
            combed_df = combed_df.append(name_df)
        except:
            continue
    # Append prices
    all_money = all_money.reset_index()
    all_money.columns = ['index','data']
    all_money['category'] = 'price ' + all_money['index'].astype(str)
    all_money = all_money.drop("index",axis=1)
    combed_df = combed_df.append(all_money)
    
    st.write("__Detected info:__")
    
    if status == 'bad':
        st.write("__Detected fees and totals:__")
        not_people
    else:
        for i, row in combed_df.iterrows():
            if row['data'] == not_people[-1]: # find total
                row['category'] = 'total' # rename total
        if len(not_people) == 6: # all fees
            for i,row in combed_df.iterrows():
                if row['data'] == not_people[-2]:
                    row['category'] = 'tip'
                if row['data'] == not_people[-3]:
                    row['category'] = 'service fee'
                if row['data'] == not_people[-4]:
                    row['category'] = 'delivery fee'
                if row['data'] == not_people[-5]:
                    row['category'] = 'tax'
                if row['data'] == not_people[-6]:
                    row['category'] = 'subtotal'
            st.table(combed_df.set_index('category'))
        if len(not_people) == 5: # no delivery fee 
            for i,row in combed_df.iterrows():
                if row['data'] == not_people[-2]:
                    row['category'] = 'tip'
                if row['data'] == not_people[-3]:
                    row['category'] = 'service fee'
                if row['data'] == not_people[-4]:
                    row['category'] = 'tax'
                if row['data'] == not_people[-5]:
                    row['category'] = 'subtotal'
            st.table(combed_df.set_index('category'))
        if len(not_people) == 3: # no delivery fee, service fee, or tip
            for i, row in combed_df.iterrows():
                if row['data'] == not_people[-2]: # find tax
                    row['category'] = 'tax' # rename tax
                if row['data'] == not_people[-3]: # find subtotal
                    row['category'] = 'subtotal' # rename subtotal
            st.table(combed_df.set_index('category'))
        else:
            # catchall, because sometimes there are 4 people and lots of fees
            ""
    st.write("__Detected cost distribution:__")
    st.write(receipt_input.title())

auto_input(gui='(Beta)')