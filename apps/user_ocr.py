# User selects items in receipt, I parse it.

from PIL import Image
import cv2
import streamlit as st
import pandas as pd
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Receipt Parser")
st.sidebar.title("Upload an Image")

receipt_img = st.sidebar.file_uploader("",type=["png","jpg","jpeg"])

# returns hex
stroke_color = st.sidebar.color_picker("Using one color for each person, select what they bought.") 
st.sidebar.info("Click the down arrow when done.")


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

if receipt_img:
    im = Image.open(receipt_img)
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
    import pytesseract as tes
    img_str = tes.image_to_string(Image.open(receipt_img))
    jpg_original = base64.b64decode(img_str)
    jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
    img = cv2.imdecode(jpg_as_np, flags=1)