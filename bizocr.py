import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
import mysql.connector as sql
from PIL import Image
import cv2
import os
import matplotlib.pyplot as plt
import re

# SETTING PAGE CONFIGURATIONS
icon = Image.open("icon.png")
st.set_page_config(page_title= "BizCardX: Extracting Business Card Data with OCR | By Sunilkumar",
                   page_icon= icon,
                   layout= "wide",
                   initial_sidebar_state= "expanded",
                   menu_items={'About': """# This OCR app is created by *sunilkumar*!"""})
st.markdown("<h1 style='text-align: center; color: red;'>BizCardX: Extracting Business Card Data with OCR</h1>", unsafe_allow_html=True)



# CREATING OPTION MENU
with st.sidebar:
    selected = option_menu(None, ["Home","Upload & Extract","Modify"], 
                        icons=["house","cloud-upload","pencil-square"],
                        default_index=0,
                        orientation="vertical",
                        styles={"nav-link": {"font-size": "25px", "text-align": "centre", "margin": "0px", "--hover-color": "#09F8F1"},
                                "icon": {"font-size": "25px"},
                                "container" : {"max-width": "6000px"},
                                "nav-link-selected": {"background-color": "#E14D41"}})

# INITIALIZING THE EasyOCR READER
reader = easyocr.Reader(['en'])

# CONNECTING WITH MYSQL DATABASE
mydb = sql.connect(host="localhost",
                   user="root",
                   password ="sunil",
                   database= "bizcard"
                  )
mycursor = mydb.cursor(buffered=True)

# TABLE CREATION
mycursor.execute('''CREATE TABLE IF NOT EXISTS card_data
                   (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    company_name TEXT,
                    card_holder TEXT,
                    designation TEXT,
                    mobile_number VARCHAR(50),
                    email TEXT,
                    website TEXT,
                    area TEXT,
                    city TEXT,
                    state TEXT,
                    pin_code VARCHAR(10),
                    image LONGBLOB
                    )''')

# HOME MENU
if selected == "Home":
    col1,col2 = st.columns([2,1])
    with col1:
        st.markdown("### :green[**Technologies Used :**] Python,easy OCR, Streamlit, SQL, Pandas")
        st.markdown("### :green[**Overview :**] In this streamlit web app you can upload an image of a business card and extract relevant information from it using easyOCR. You can view, modify or delete the extracted data in this app. This app would also allow users to save the extracted information into a database along with the uploaded business card image. The database would be able to store multiple entries, each with its own business card image and extracted information.")
    with col2:
        st.image("home.jpg")

# UPLOAD AND EXTRACT MENU
if selected == "Upload & Extract":
    st.markdown("### :Upload a Business Card")
    uploded_card = st.file_uploader("upload here",label_visibility="collapsed",args=(1,2,3,4),type=["png","jpeg","jpg"])
    
    if uploded_card is not None:
        
        def save_card(uploded_card):
            with open(os.path.join("Creative Modern Business Card",uploded_card.name), "wb") as f:
                f.write(uploded_card.getbuffer())   
        save_card(uploded_card)
        
        def image_preview(image,res): 
            for (bbox, text, prob) in res: 
            # unpack the bounding box
                (tl, tr, br, bl) = bbox
                tl = (int(tl[0]), int(tl[1]))
                tr = (int(tr[0]), int(tr[1]))
                br = (int(br[0]), int(br[1]))
                bl = (int(bl[0]), int(bl[1]))
                cv2.rectangle(image, tl, br, (0, 255, 0), 2)
                cv2.putText(image, text, (tl[0], tl[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            plt.rcParams['figure.figsize'] = (10,10)
            plt.axis('off')
            plt.imshow(image)

                    
                
        #easy OCR
        saved_img = os.getcwd()+ "\\" + "Creative Modern Business Card"+ "\\"+ uploded_card.name
        result = reader.readtext(saved_img,detail = 0,paragraph=False)
        
        # CONVERTING IMAGE TO BINARY TO UPLOAD TO SQL DATABASE
        def img_to_binary(file):
            # Convert image data to binary format
            with open(file, 'rb') as file:
                binaryData = file.read()
            return binaryData
        image_binary = img_to_binary(saved_img)
        
        data = {"company_name" : [],
                "card_holder" : [],
                "designation" : [],
                "mobile_number" :[],
                "email" : [],
                "website" : [],
                "area" : [],
                "city" : [],
                "state" : [],
                "pin_code" : [],
                "image" : img_to_binary(saved_img)
            }

        def get_data(res):
            for ind,i in enumerate(res):

                # To get WEBSITE_URL
                if "www " in i.lower() or "www." in i.lower():
                    data["website"].append(i)
                elif "WWW" in i:
                    data["website"] = res[4] +"." + res[5]

                # To get EMAIL ID
                elif "@" in i:
                    data["email"].append(i)

                # To get MOBILE NUMBER
                elif "-" in i:
                    data["mobile_number"].append(i)
                    if len(data["mobile_number"]) ==2:
                        data["mobile_number"] = " & ".join(data["mobile_number"])

                # To get COMPANY NAME  
                elif ind == len(res)-1:
                    data["company_name"].append(i)

                # To get CARD HOLDER NAME
                elif ind == 0:
                    data["card_holder"].append(i)

                # To get DESIGNATION
                elif ind == 1:
                    data["designation"].append(i)

                # To get AREA
                if re.findall('^[0-9].+, [a-zA-Z]+',i):
                    data["area"].append(i.split(',')[0])
                elif re.findall('[0-9] [a-zA-Z]+',i):
                    data["area"].append(i)

                # To get CITY NAME
                match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                match3 = re.findall('^[E].*',i)
                if match1:
                    data["city"].append(match1[0])
                elif match2:
                    data["city"].append(match2[0])
                elif match3:
                    data["city"].append(match3[0])

                # To get STATE
                state_match = re.findall('[a-zA-Z]{9} +[0-9]',i)
                if state_match:
                    data["state"].append(i[:9])
                elif re.findall('^[0-9].+, ([a-zA-Z]+);',i):
                    data["state"].append(i.split()[-1])
                if len(data["state"])== 2:
                    data["state"].pop(0)

                # To get PINCODE        
                if len(i)>=6 and i.isdigit():
                    data["pin_code"].append(i)
                elif re.findall('[a-zA-Z]{9} +[0-9]',i):
                    data["pin_code"].append(i[10:])
        get_data(result)
        
        #FUNCTION TO CREATE DATAFRAME
        def create_df(data):
            df = pd.DataFrame(data)
            return df
        df = create_df(data)
        st.success("### Data Extracted!")
        st.write(df)

        # DISPLAYING THE UPLOADED CARD
        if st.button("Preview"):
            col1,col2 = st.columns(2,gap="large")
            with col1:
                st.markdown("#     ")
                st.markdown("#     ")
                st.markdown("### You have uploaded the card")
                st.image(uploded_card)
            # DISPLAYING THE CARD WITH HIGHLIGHTS
            with col2:
                st.markdown("#     ")
                st.markdown("#     ")
                with st.spinner("Please wait processing image..."):
                    st.set_option('deprecation.showPyplotGlobalUse', False)
                    saved_img = os.getcwd()+ "\\" + "Creative Modern Business Card"+ "\\"+ uploded_card.name
                    image = cv2.imread(saved_img)
                    res = reader.readtext(saved_img)
                    st.markdown("### Image Processed and Data Extracted")
                    st.pyplot(image_preview(image,res))  

    
    if st.button("Upload to Database"):
        try:
            for i, row in df.iterrows():
                # Check if the entry exists before inserting it
                query = f"SELECT * FROM card_data WHERE company_name='{row['company_name']}' AND card_holder='{row['card_holder']}' AND designation='{row['designation']}' AND mobile_number='{row['mobile_number']}' AND email='{row['email']}' AND website='{row['website']}' AND area='{row['area']}' AND city='{row['city']}' AND state='{row['state']}' AND pin_code='{row['pin_code']}'"
                mycursor.execute(query)
                result = mycursor.fetchone()
                if not result:  # If entry doesn't exist, insert it
                    sql = """INSERT INTO card_data(company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,image)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                    mycursor.execute(sql, (row['company_name'], row['card_holder'], row['designation'], row['mobile_number'], row['email'], row['website'], row['area'], row['city'], row['state'], row['pin_code'], image_binary))
                    mydb.commit()
                    st.success("#### Uploaded to database successfully!")
                else:
                    st.warning("Data already exists in the database.")

            
        except Exception as e:
            st.error(f"Error: {e}")

# MODIFY MENU    
if selected == "Modify":
    Option = st.sidebar.selectbox("**Options**", ("Update", "Delete"))
    if Option=="Update":
        mycursor.execute("SELECT card_holder FROM card_data")
        result = mycursor.fetchall()
        business_cards = {}
        for row in result:
            business_cards[row[0]] = row[0]
        selected_card = st.selectbox("Select a card holder name to update", list(business_cards.keys()))


        # Fetch details of the selected card from the database
        mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data WHERE card_holder=%s",
                        (selected_card,))
        result = mycursor.fetchone()

        st.write("### Details for selected card holder:")
        company_name = st.text_input("Company_Name", result[0])
        card_holder = st.text_input("Card_Holder", result[1])
        designation = st.text_input("Designation", result[2])
        mobile_number = st.text_input("Mobile_Number", result[3])
        email = st.text_input("Email", result[4])
        website = st.text_input("Website", result[5])
        area = st.text_input("Area", result[6])
        city = st.text_input("City", result[7])
        state = st.text_input("State", result[8])
        pin_code = st.text_input("Pin_Code", result[9])

        if st.button("Commit changes to DB"):
            try:
                # Update the information for the selected business card in the database
                mycursor.execute("""UPDATE card_data SET company_name=%s,card_holder=%s,designation=%s,mobile_number=%s,email=%s,website=%s,area=%s,city=%s,state=%s,pin_code=%s
                                    WHERE card_holder=%s""", (company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,selected_card))
                mydb.commit()
                st.success("Information updated in database successfully.")
            except Exception as e:
                st.error(f"Error: {e}")

    if Option=="Delete":
        try:
            mycursor.execute("SELECT card_holder FROM card_data")
            result = mycursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to Delete", list(business_cards.keys()))

            st.write(f"### You have selected :red[**{selected_card}'s**] card to delete")
            st.write("#### Proceed to delete this card?")

            if st.button("Yes Delete Business Card"):
                mycursor.execute(f"DELETE FROM card_data WHERE card_holder='{selected_card}'")
                mydb.commit()
                st.success("Business card information deleted from database.")
        except:
            st.warning("There is no data available in the database")
        
        if st.button("View updated data"):
            mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data")
            updated_df = pd.DataFrame(mycursor.fetchall(),columns=["Company_Name","Card_Holder","Designation","Mobile_Number","Email","Website","Area","City","State","Pin_Code"])
            st.write(updated_df)