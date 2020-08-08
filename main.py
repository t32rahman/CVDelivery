# Dependancies
import os, io, cv2, smtplib, imghdr
import pandas as pd
import numpy as np
from google.cloud import vision
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Google Service Token
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'ServiceAccountToken.json'

client =  vision.ImageAnnotatorClient()

# This determines the minimum threshold for movement detection. 
# The higher the value, the more likely it is ignore background <--- Great for blocking out sidewalk movement
SENSITIVITY = 2000 

# Initializing video input
cap = cv2.VideoCapture(0)
ret, frame1 = cap.read()
ret, frame2 = cap.read()
count = 0 # used as a proxy for measuring time because camera is set to 60 frames per sec (so count = 60 means approx. 1 sec)

# Email credentials
email_user = '' #### Must be set up prior to running ####
email_pass = '' #### Must be set up prior to running ####
email_send = input('Please enter your email address:')



# Fucntion is used to send out the Package delivered message
def sendNotification():
    subject = "A Package has been Delivered!"

    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_send
    msg['Subject'] = subject

    body = 'Hi there, We have detected that a Package has been delivered to your doorstep. We highly recommend that you pick it up as soon as possible to reduce the chances of it getting stolen. Not home? Call a neighbour to pick it up for you.'
    msg.attach(MIMEText(body,'plain'))

    filename = 'Images/frame.jpg'
    attachment = open(filename, 'rb')

    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= "+filename)

    msg.attach(part)
    text = msg.as_string()
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_user,email_pass)

    server.sendmail(email_user, email_send, text)
    server.quit()

# Checking for package delivery related labels
def chkLabels (df):
    c1 = False
    c2 = False
    c3 = False
    for index, row in df.iterrows():
        if row['score'] > 60:
            desc = ''.join(row['description'])
            if desc == "Package delivery":
                c1 = True
            if (desc == "Warehouseman") or (desc == "Person"):
                c2 = True
            if (desc == "Box") or (desc == "Packaged goods") or (desc == "Mail") or (desc == "Packing and labeling") or (desc == "Carton"):
                c3 = True
    if c1 or (c2 and c3):
        # if all conditions are satisfied == a package has been delivered, and a notification is sent
        sendNotification()
        print("Sent Notification \n")


# main capture loop
while cap.isOpened():

    # movement detection
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, thresh = cv2.threshold(blur, 20, 355, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=3)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        (x, y, w, h) = cv2.boundingRect(contour)
        
        # Ignores all movement under minimum sensitivity threshold
        if cv2.contourArea(contour) < SENSITIVITY:
            continue
        cv2.rectangle(frame1, (x,y), (x+w, y+h), (0, 255,0), 2)

        count+=1
        if  count > 300:
            # takes a snapshot if there is continous movement for 5 sec
            cv2.imwrite('./Images/frame.jpg',frame2)
            image_path = f'./Images/frame.jpg'
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()

            # Sends snapshot to Google Cloud Vision API
            image = vision.types.Image(content=content)
            response = client.label_detection(image=image)
            labels = response.label_annotations

            # Stores all the returned labels from GCVA
            df = pd.DataFrame(columns=['description', 'score', 'topicality'])
            for label in labels:
                df = df.append(
                    dict(
                        description = label.description,
                        score=label.score,
                        topicality=label.topicality
                    ), ignore_index=True
                )
            print(df)
            chkLabels(df)
            count = 0

    # displays the frame with rectangles and then moves onto the next frame before looping
    cv2.imshow("feed", frame1)
    frame1 = frame2
    ret, frame2 = cap.read()

    # presss "esc" to escape the program
    if cv2.waitKey(40) == 27:
        break

cv2.destroyAllWindows()
cap.release()
