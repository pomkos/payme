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
    text_str = text_str.lower().split("\n")
    text_str = pd.Series(text_str)

    # get rid of empty rows
    text_str = text_str.replace('',float('NaN'))
    text_str = text_str.dropna().reset_index(drop=True)
    
    return text_str

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
    st.write('Leave the typing, calculating, and requesting up to us!')
    my_receipt = st.file_uploader("Upload a screenshot or receipt",type=['png','jpg','jpeg','pdf'])
    if not my_receipt:
        st.info("Upload a screenshot of the full DoorDash receipt!")
        st.info("Make sure everything from 'Group Order' downwards is visible.")
        st.image('images/sample_receipt.jpg',caption='Sample receipt',width=150)
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
    extracted = {} # dictionary of all extracted info
    ###
    # Extract all prices
    ###
    monies = text_str[text_str.str.contains("\$")]
    try:
        monies = monies.str.replace('$','').astype(float)
    except:
        st.info("Currently only supporting group DoorDash orders. Try manual input!")
        st.stop()
    extracted['monies'] = monies.reset_index(drop=True)
    
    ### 
    # Extract people
    ###    
    # number of people
    parts = text_str[text_str.str.contains('participants')]
    extracted['participants'] = int(list(parts.str.extract("(\d\d?) participants")[0])[0])
    extracted['items'] = int(list(parts.str.extract("(\d\d?) items")[0])[0])
    
    my_names = st.text_input("Write names below, separated by a comma. Ex: peter, Russell")
    if not my_names:
        st.info(f"""Add all __{extracted['participants']} names__, separated by a comma, in the order that they appear on the receipt.""")
        st.info(f"Click 'OCR feedback' to see your uploaded image")
        st.stop()
    my_names = my_names.split(',')
    if len(my_names)!=extracted['participants']:
        # if user didn't provide the right number of names, script won't work
        st.warning(f"I detected __{extracted['participants']}__ people on this receipt, but you provided __{len(my_names)}__")
        st.stop()
    
    # format input to remove space and make it all lowercase
    names = [n.lower().strip() for n in my_names]
    names.append('subtotal')
    names = tuple(names)
    names_dict = {} # dictionary of names and their iloc in the series
    for i, s in text_str.iteritems():
        for name in names:
            if s.startswith(name):
                names_dict[name] = i
    # number of items per person
    for i in range(len(names)):
        # find how many food items each person ate
        try:
            start = names_dict[names[i]]
            end = names_dict[names[i+1]]
            extracted[names[i]] = len(text_str[start+1:end])
        except:
            pass

    ###
    # Extract costs per person
    ###
    all_money = extracted['monies'] # each item is on its own line
    people_money = all_money.loc[:extracted['items']-1] # the first X rows are all items, subtract one cuz ending is inclusive
    my_receipt = {}
    try:
        for name in names[:len(names)-1]: # the last one is always subtotal
            my_receipt[name] = people_money.loc[:extracted[name]-1]
            for i in range(extracted[name]):
                try:
                    people_money = people_money.drop(i)
                except:
                    pass
            people_money = people_money.reset_index(drop=True)
    except:
        st.warning("Are you sure the names were provided in the right order?")
    receipt_input = ''
    for name in my_receipt.keys():
        receipt_input += f'{name}: {list(my_receipt[name])} '
    receipt_input = receipt_input.replace('[','')
    receipt_input = receipt_input.replace(']','')
    ###
    # Extract totals, fees, tips, taxes
    ###
    not_people = tuple(all_money.loc[extracted['items']:]) # since each item is on its own line, the number of items is a good cutoff
     
    if len(not_people) == 6: # delivery fee assumed to be included
        subtotal = not_people[0]
        tax_input = not_people[1]
        fees_input = not_people[2]
        fees_input += not_people[3]
        tip_input = not_people[4]
        total = not_people[5]
        with col_extract:
            st.success("Data extracted!")
            extracted_col(extracted,all_money,not_people,receipt_input,names)  
    elif len(not_people) == 5: # if there are only 5, then no delivery fee was included
        subtotal = not_people[0]
        tax_input = not_people[1]
        fees_input = not_people[2]
        tip_input = not_people[3]
        total = not_people[4]
        with col_extract:
            st.success("Data extracted!")
            extracted_col(extracted,all_money,not_people,receipt_input,names)       
    elif len(not_people) == 3: # this was a pickup order, so no fees or tip
        subtotal = not_people[0]
        tax_input = not_people[1]
        fees_input = 0
        tip_input = 0
        total = not_people[2]
        with col_extract:
            st.success("Data extracted!")
            extracted_col(extracted,all_money,not_people,receipt_input,names) 
    elif len(not_people) == 4: # subtotal not detected, no delivery fee
        with col_extract:
            st.warning("I don't think I found the subtotal")
            extracted_col(extracted,all_money,not_people,receipt_input,names) 
        subtotal = 0
        tax_input = not_people[0]
        fees_input = not_people[1]
        tip_input = not_people[2]
        total = not_people[3]
    else:
        import pandas as pd
        st.warning(f"Expected 5 or 6 nonFood items, but found {len(not_people)}. Try manual input instead!")
        with col_extract:
            st.warning("Something went wrong. Did I OCR right?")
            extracted_col(extracted,all_money,not_people,receipt_input,names, status = 'bad')
        st.stop()
          
    return receipt_input ,fees_input, tax_input, tip_input

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
            st.write(not_people)
    st.write("__Detected cost distribution:__")
    st.write(receipt_input.title())

auto_input(gui='(Beta)')