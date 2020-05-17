import os, io, cv2, smtplib, imghdr
import pandas as pd
import numpy as np
from google.cloud import vision
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'ServiceAccountToken.json'

client =  vision.ImageAnnotatorClient()

SENSITIVITY = 2000

cap = cv2.VideoCapture(0)
ret, frame1 = cap.read()
ret, frame2 = cap.read()
count = 0

email_user = 'emailistnn@gmail.com'
email_pass = 'Tata2001'
email_send = input('Please enter your email address:')
email_sendpass = input('Please enter your a new password:')

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

def chkLabels (df):
    c1 = False
    c2 = False
    c3 = False
    for index, row in df.iterrows():
        #if row['score'] > 50:
        desc = ''.join(row['description'])
        if desc == "Package delivery":
            c1 = True
        if (desc == "Warehouseman") or (desc == "Person"):
            c2 = True
        if (desc == "Box") or (desc == "Packaged goods") or (desc == "Mail") or (desc == "Packing and labeling") or (desc == "Carton"):
            c3 = True
    if c1 or (c2 and c3):
        sendNotification()
        print("Sent Notification \n")


while cap.isOpened():
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, thresh = cv2.threshold(blur, 20, 355, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=3)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        (x, y, w, h) = cv2.boundingRect(contour)
        
        if cv2.contourArea(contour) < SENSITIVITY:
            continue
        cv2.rectangle(frame1, (x,y), (x+w, y+h), (0, 255,0), 2)
        # cv2.putText(frame1, "Status: {}".format('Movement'), (10, 20), cv2.FONT_HERSHEY_SIMPLEX,
        #             1, (0, 0, 255), 3)
        count+=1
        if  count > 300:
            cv2.imwrite('./Images/frame.jpg',frame2)
            image_path = f'./Images/frame.jpg'
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()

            image = vision.types.Image(content=content)
            response = client.label_detection(image=image)
            labels = response.label_annotations

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


        
    #cv2.drawContours(frame1, contours, -1,  (0,255,0), 2)

    cv2.imshow("feed", frame1)
    frame1 = frame2
    ret, frame2 = cap.read()

    if cv2.waitKey(40) == 27:
        break

cv2.destroyAllWindows()
cap.release()
