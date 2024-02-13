# import

import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import streamlit as st
from streamlit_option_menu import option_menu
import sqlite3



def image_to_text(path):

    input_img= Image.open(path)

    #converting image to array formet
    image_arr= np.array(input_img)

    reader= easyocr.Reader(['en'])
    text= reader.readtext(image_arr, detail=0)
    return text,input_img


def extracted_text(texts):
    extrd_dict = {"NAME":[],"DESIGNATION":[],"COMPANY_NAME":[],"CONTACT":[],"EMAIL":[],
                  "WEBSITE":[],"ADDRESS":[],"PINCODE":[]}
    extrd_dict["NAME"].append(texts[0])
    extrd_dict["DESIGNATION"].append(texts[1])

    for i in range(2,len(texts)):
        if texts[i].startswith("+") or (texts[i].replace("-","").isdigit() and '-' in texts[i]):
            extrd_dict["CONTACT"].append(texts[i])

        elif "@" in texts[i] and ".com" in texts[i]:
            small =texts[i].lower()
            extrd_dict["EMAIL"].append(small)

        elif "WWW" in texts[i] or "www" in texts[i] or "Www" in texts[i] or "wWw" in texts[i] or "wwW" in texts[i]:
            small = texts[i].lower()
            extrd_dict["WEBSITE"].append(small)

        elif "Tamil Nadu" in texts[i]  or "TamilNadu" in texts[i] or texts[i].isdigit():
            extrd_dict["PINCODE"].append(texts[i])

        elif re.match(r'^[A-Za-z]',texts[i]):
            extrd_dict["COMPANY_NAME"].append(texts[i])

        else:
            remove_colon = re.sub(r'[,;]', '', texts[i])
            extrd_dict["ADDRESS"].append(remove_colon)

    for key,value in extrd_dict.items():
        if len(value)>0:
            concadenate = ' '.join(value)
            extrd_dict[key] = [concadenate]
        else:
            value = 'NA'
            extrd_dict[key] = [value]

    return extrd_dict


# Streamlit Part

# SETTING PAGE CONFIGURATIONS
icon = Image.open("/content/card.png")
st.set_page_config(page_title="BizCardX: Extracting Business Card Data with OCR",
                   page_icon=icon,
                   layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={'About': """# This OCR app is created by *APOORVA KHARE*!"""})
st.markdown("<h1 style='text-align: center; color: Green;'>BizCardX: Extracting Business Card Data with OCR</h1>",
            unsafe_allow_html=True)

# SETTING-UP BACKGROUND IMAGE
def setting_bg():
    st.markdown(f""" <style>.stApp {{
                        background:url("https://wallpapers.com/images/featured/plain-zoom-background-d3zz0xne0jlqiepg.jpg");
                        background-size: cover}}
                     </style>""", unsafe_allow_html=True)


setting_bg()

# CREATING OPTION MENU
select = option_menu(None, ["Home", "Upload & Modify", "Delete"],
                       icons=["house", "cloud-upload", "pencil-square"],
                       default_index=0,
                       orientation="horizontal",
                       styles={"nav-link": {"font-size": "35px", "text-align": "centre", "margin": "-3px",
                                            "--hover-color": "#545454"},
                               "icon": {"font-size": "35px"},
                               "container": {"max-width": "6000px"},
                               "nav-link-selected": {"background-color": "#ff5757"}})

# HOME MENU
if select == "Home":
    col1, col2 = st.columns(2)
    with col1:
        st.image(Image.open("/content/card.png"), width=300)
        st.markdown("## :green[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")
    with col2:
        st.write(
            "## :green[**About :**] Bizcard is a Python application designed to extract information from business cards.")
        st.write(
            '## The main purpose of Bizcard is to automate the process of extracting key details from business card images, such as the name, designation, company, contact information, and other relevant data. By leveraging the power of OCR (Optical Character Recognition) provided by EasyOCR, Bizcard is able to extract text from the images.')

elif select == "Upload & Modify":

    img= st.file_uploader("Upload the Image", type= ["png", "jpg", "jpeg"], label_visibility= "hidden")

    if img is not None:

        st.image(img,width= 300)

        text_image,input_img= image_to_text(img)

        text_dict= extracted_text(text_image)

        if text_dict:
            st.success("TEXT IS EXTRACTED SUCCESSFULLY")

      # creating dataframe
        text_dict= extracted_text(text_image)
        df = pd.DataFrame(text_dict)
        st.dataframe(df)
        # Converting image into bytes
        Image_bytes= io.BytesIO()
        input_img.save(Image_bytes,format= "PNG")
        image_data= Image_bytes.getvalue()
        # Creating dictionary
        data = {"Image": [image_data]}
        df_1 = pd.DataFrame(data)
        concat_df = pd.concat([df, df_1], axis=1)

        # Database
        text_dict = extracted_text(text_image)
        df = pd.DataFrame(text_dict)
        selected= st.radio("Select the Option",["None","Upload","Modify"])
        if selected == "None":
          st.write("")

        if selected == "Modify":
            col_1, col_2 = st.columns([4, 4])
            with col_1:
                modified_n = st.text_input('Name', text_dict["NAME"][0])
                modified_d = st.text_input('Designation', text_dict["DESIGNATION"][0])
                modified_c = st.text_input('Company_Name', text_dict["COMPANY_NAME"][0])
                modified_con = st.text_input('Contact', text_dict["CONTACT"][0])
                concat_df["NAME"], concat_df["DESIGNATION"], concat_df["COMPANY_NAME"], concat_df[
                    "CONTACT"] = modified_n, modified_d, modified_c, modified_con
            with col_2:
                modified_m = st.text_input('Email', text_dict["EMAIL"][0])
                modified_w = st.text_input('Website', text_dict["WEBSITE"][0])
                modified_a = st.text_input('Address', text_dict["ADDRESS"][0])
                modified_p = st.text_input('Pincode', text_dict["PINCODE"][0])
                concat_df["EMAIL"], concat_df["WEBSITE"], concat_df["ADDRESS"], concat_df[
                    "PINCODE"] = modified_m, modified_w, modified_a, modified_p

            col3, col4 = st.columns([4, 4])
            with col3:
                Preview = st.button("Preview modified text")
            with col4:
                Upload = st.button("Upload")
            if Upload:
              with st.spinner("In progress"):
                  conn = sqlite3.connect('bizcardx.db')

                  table_name = 'bizcard_details'
                  # Define the table creation query
                  create_table_query = '''
                  CREATE TABLE IF NOT EXISTS bizcard_details(
                      NAME varchar(225),
                      DESIGNATION varchar(225),
                      COMPANY_NAME varchar(225),
                      CONTACT varchar(225),
                      EMAIL text,
                      WEBSITE text,
                      ADDRESS text,
                      PINCODE varchar(225)
                  )'''

                  conn.execute(create_table_query)
                  conn.commit()


                  for index, row in concat_df.iterrows():
                      insert_query = '''
                              INSERT INTO bizcard_details
                      VALUES (?,?,?,?,?,?,?,?)
                      '''
                      values= (row['NAME'], row['DESIGNATION'], row['COMPANY_NAME'], row['CONTACT'],
                              row['EMAIL'], row['WEBSITE'], row['ADDRESS'], row['PINCODE'])

                      # Execute the insert query
                      conn.execute(insert_query,values)

                      # Commit the changes
                      conn.commit()

                      query = 'SELECT * FROM bizcard_details'.format(table_name)

                      df_from_sqlite = pd.read_sql_query(query, conn)

                      st.dataframe(df_from_sqlite)

                      if st.dataframe:
                          st.success("UPLOADED SUCCESSFULLY")
            if Preview:
                filtered_df = concat_df[
                    ['NAME', 'DESIGNATION', 'COMPANY_NAME', 'CONTACT', 'EMAIL', 'WEBSITE', 'ADDRESS', 'PINCODE']]
                st.dataframe(filtered_df)
            else:
                pass

        if selected == "Upload":
              with st.spinner("In progress"):
                  conn = sqlite3.connect('bizcardx.db')

                  table_name = 'bizcard_details'
                  # Define the table creation query
                  create_table_query = '''
                  CREATE TABLE IF NOT EXISTS bizcard_details(
                      NAME varchar(225),
                      DESIGNATION varchar(225),
                      COMPANY_NAME varchar(225),
                      CONTACT varchar(225),
                      EMAIL text,
                      WEBSITE text,
                      ADDRESS text,
                      PINCODE varchar(225)
                  )'''

                  conn.execute(create_table_query)
                  conn.commit()


                  for index, row in concat_df.iterrows():
                      insert_query = '''
                              INSERT INTO bizcard_details
                      VALUES (?,?,?,?,?,?,?,?)
                      '''
                      values= (row['NAME'], row['DESIGNATION'], row['COMPANY_NAME'], row['CONTACT'],
                              row['EMAIL'], row['WEBSITE'], row['ADDRESS'], row['PINCODE'])

                      # Execute the insert query
                      conn.execute(insert_query,values)

                      # Commit the changes
                      conn.commit()

                      query = 'SELECT * FROM bizcard_details'.format(table_name)

                      df_from_sqlite = pd.read_sql_query(query, conn)

                      st.dataframe(df_from_sqlite)

                      if st.dataframe:
                          st.success("UPLOADED SUCCESSFULLY")


if select == "Delete":
    with st.spinner("In Progress"):
        conn = sqlite3.connect('bizcardx.db')
        cursor= conn.cursor()

        col1,col2= st.columns([4,4])
        with col1:
            cursor.execute("SELECT NAME FROM bizcard_details")
            conn.commit()
            table1= cursor.fetchall()

            names=[]

            for i in table1:
                names.append(i[0])

            name_select= st.selectbox("Select the Name to be deleted ",options= names)

        with col2:
            cursor.execute(f"SELECT DESIGNATION FROM bizcard_details WHERE NAME ='{name_select}'")
            conn.commit()
            table2= cursor.fetchall()

            designations= []

            for j in table2:
                designations.append(j[0])

            designation_select= st.selectbox("Select the Designation of the chosen name", options= designations)
            st.markdown(" ")

            col_a, col_b, col_c = st.columns([3, 3, 3])
        with col_b:
            remove = st.button("Click here to delete")
        if name_select and designation_select and remove:
            col1,col2,col3= st.columns(3)

            with col1:
              st.write(f"Selected Name : {name_select}")
              st.write("")
              st.write("")

              st.write(f"Selected Designation : {designation_select}")
            with col2:
              st.write("")
              st.write("")
              st.write("")
              st.write("")

              if remove:
                    conn.execute(f"DELETE FROM bizcard_details WHERE NAME ='{name_select}' AND DESIGNATION = '{designation_select}'")
                    conn.commit()

                    st.warning("CARD DELETED", icon="⚠️")
