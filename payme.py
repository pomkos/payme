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
st.set_page_config(page_title="Venmo Calculator")
# st.markdown(hide_streamlit_style, unsafe_allow_html=True) # hides the hamburger menu


def start():
    """
    Thalamus. Creates the GUI and redirects requests to the appropriate scripts. The Thalamus.
    """
    st.sidebar.write('[Github](https://github.com/pomkos/payme)')
    action = st.sidebar.radio(
        "Choose an action", options=["Get venmo links", "Claim meals", "Submit receipt"]
    )

    if action == "Get venmo links":
        select_input = "release"  # disabled user section of payme ('alpha' to activate)
        service_chosen = st.sidebar.radio(
            "Choose input type", options=["Manual Mode", "Delivery App"]
        )

        if "Manual" not in service_chosen:
            user_output = delivery_brain()
        else:
            user_output = mm.manual_mode()

        total_input, data = calc.total_calculator(**user_output)
        # dictionary of kwargs for venmo_calc()
        user_modified = {
            "tax": user_output["tax_input"],
            "tip": user_output["tip_input"],
            "misc_fees": user_output["fees_input"],
            "description": user_output["description"],
            "total": total_input,
            "discount": user_output["discount"],
            "contribution": user_output["contribution"],
            "my_dic": data,
        }
        try:
            calc_message = calc.venmo_calc(**user_modified)
            calc.html_table(calc_message["messages"], calc_message["request_money"])

        except ZeroDivisionError:
            st.info("See the how to for more information!")
            calc_message = {"request_money": None}
            st.stop()
    elif action == "Claim meals":
        from apps import food_select as fs

        st.title("Claim your Meal!")
        st.write("Let everyone know what you ordered and/or shared.")
        sf = fs.labelFood()
    else:
        from apps import food_select as fs

        st.title("Complex Receipt Receiver")
        st.write("For when receipts are too complex to sort who got what")
        rr = fs.receiptReceiver()


def delivery_brain():
    """
    Instructions and web GUI to for web receipts, including logic to detect doordash vs ubereats.
    """
    ##########
    # HOW TO #
    ##########
    st.title("Venmo Requests Calculator: Delivery App Mode")
    st.write(
        "Give us the DoorDash or UberEats receipt, we'll spit out some venmo request links!"
    )
    with st.expander("How To"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(
                """
            __DoorDash__

            1. Copy and paste the entire contents of DoorDash receipt from __Order Details__ at the top to the __Total__ at the bottom.
            2. Follow the prompts """
            )
            st.write("")
            st.markdown(
                "![DoorDash copy instructions](https://github.com/pomkos/payme/raw/main/images/copy_dd.gif)"
            )
        with col2:
            st.write(
                """
            __UberEats__

            1. Copy and paste the entire contents of UberEats receipt from __Total__ at the top to __Tip__ at the bottom.
            2. Once pasted, make sure names are on separate lines.
            3. Follow the prompts"""
            )
            st.write("")
            st.markdown(
                "![UberEats copy gif placeholder](https://github.com/pomkos/payme/raw/main/images/copy_ue.gif)"
            )
    #######
    # GUI #
    #######
    description = st.text_input("(Optional) Description, like the restaurant name")
    receipt = st.text_area(
        "Paste the entire receipt from your service, including totals and fees",
        height=300,
    )
    receipt = receipt.lower()

    if not receipt:
        st.info("See the how to for more information!")
        st.stop()

    #########
    # LOGIC #
    #########
    try:
        if "(you)" in receipt.lower():  # ubereats has this
            st.info("This looks like an UberEats receipt.")
            deny = st.checkbox("It's actually DoorDash")
            if deny:
                service_chosen = "doordash"
            else:  # its ubereats
                service_chosen = "ubereats"
                receipt = receipt.replace(",", "")
        elif "participant" in receipt:  # doordash
            st.info("This looks like a DoorDash receipt.")
            deny = st.checkbox("It's actually UberEats")
            if deny:
                service_chosen = "ubereats"
            else:
                service_chosen = "doordash"
        else:
            st.error(
                "Unknown delivery app. See the how to, try the manual mode, or contact Pete to request support for the receipt!"
            )
            st.stop()
        my_names = mm.name_finder(
            receipt
        )  # the name finder is located in manual_mode.py file
        service_chosen = service_chosen.lower()
        if "door" in service_chosen:
            from apps import doordash as dd

            user_output = dd.app(receipt, my_names, description)
        elif "uber" in service_chosen:
            from apps import ubereats as ue

            user_output = ue.app(receipt, my_names, description)
        return user_output
    except Exception as e:
        st.write(e)
        st.stop()


def app():
    """
    Only purpose is to start the app from bash script. Own function so the rest of the functions can be organized in a logical way.
    """
    start()


app()
