import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

email_user = 'emailistnn@gmail.com'
email_pass = 'Tata2001'
email_send = 'emailistnn@gmail.com'
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