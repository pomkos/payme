# User selects items in receipt, I parse it.

from PIL import Image
import cv2
import numpy as np
import pytesseract as tes
import streamlit as st
import pandas as pd
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Receipt Parser")
st.sidebar.title("Upload an Image")

receipt_img = st.sidebar.file_uploader("",type=["png","jpg","jpeg"])

if not receipt_img:
    st.stop()
    
im1 = Image.open(receipt_img)
width, height = im1.size

# resize if too big
if width >= 1000:
    im = im1.resize((int(width*0.25),int(height*0.25)))
elif (width < 1000) & (width > 700):
    im = im1.resize((int(width*0.5),int(height*0.5)))
else:
    im = im1

def get_rgb(hex_str, transparent = True):
    '''
    Converts hex to rgb, makes it transparent if needed
    Source: https://stackoverflow.com/a/29643643/9866659
    '''
    box_color = hex_str.replace("#","")
    rgb_box = list(int(box_color[i:i+2], 16) for i in (0, 2, 4))
    
    if transparent:
        rgb_box = rgb_box + [0.2] # add transparency to list
        
    return tuple(rgb_box) # return as tuple

def get_coords(im):
    # returns hex
    stroke_color = st.sidebar.color_picker("Using one color for each person, select what they bought. Use '#FF09E9' for totals, tips, fees") 
    st.sidebar.info("Click the down arrow when done.")

    canvas_image = st_canvas(
        fill_color = f"rgba{get_rgb(stroke_color)}",
        stroke_width = 2, # width of drawing brush
        stroke_color = stroke_color, # color of brush in hex
        background_image = im, # Pillow image to display, auto
        update_streamlit = False, # send data only when submitted
        width = im.width, # default 400
        height = im.height, # default 600
        drawing_mode = "rect", # can be freedraw, line, rect, circle, transform
        key = "canvas", # optional str to use as unique key for widget
    )

    if canvas_image.json_data is not None:
        #st.write(canvas_image.json_data)
        canvas_df = pd.json_normalize(canvas_image.json_data['objects'])
        relevant_df = canvas_df.loc[:,"originX":"stroke"]
        relevant_df = relevant_df.rename({
            'originX':'origin_x',
            'originY':'origin_y'},axis=1)
        relevant_df = relevant_df[relevant_df['height']!=0]
        st.table(relevant_df)
        return relevant_df


def app():
    relevant_df = get_coords(im)

            
    # have opencv turn img to np array from uploadedfile type
    img_array = np.array(im)
    # crop image
    all_prices = {}
    for user in range(len(relevant_df)):
        left = relevant_df.loc[user,'left']
        top = relevant_df.loc[user,'top']
        width = relevant_df.loc[user,'width']
        height = relevant_df.loc[user,'height']

        img_crp = img_array[top:top+height,left:left+width]
        # return image to user
        st.image(img_crp)
        # OCR image
        text_str = tes.image_to_string(Image.fromarray(img_crp))
        text_str = text_str.replace(' ','')
        text_str = text_str.replace('\n','')
        if text_str:
            import re
            extr_prices = re.findall("\$(\d+\.\d+)",text_str)
            # turn to numeric
            extr_prices = list(pd.to_numeric(extr_prices))
            print(text_str)
            all_prices[f'user_{user}'] = extr_prices
        else:
            all_prices[f'user_{user}'] = "Not found"
    all_prices

app()