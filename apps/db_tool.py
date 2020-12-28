# Everything you need to mess with the dataset

def adv_settings():
    '''
    Shows an expander with option to submit data to database
    '''
    with st.beta_expander("Advanced settings"):
        st.write("Not required, but very fun")
        col_save,col_show = st.beta_columns([0.33,1])

        with col_show:
            button_show = st.button(label='Preview the Database')
        with col_save:
            button_save = st.button(label='Submit to Database')

        try:
            if button_save == True:
                ### THIS IS WHERE ITEMIZED SHOULD BE SAVED
                saveus = saveInfo(my_total, my_food, tip_perc, tax_perc, fee_part,showme='no')
                saveus.save_table()
                st.balloons()

            if button_show == True:
                showus = saveInfo()
                dataframe = showus.read_table()
                dataframe = dataframe.iloc[:,1:]
                show_me = dataframe.tail()
                st.table(show_me)
        except:
            st.info("Database function down, come back later.")