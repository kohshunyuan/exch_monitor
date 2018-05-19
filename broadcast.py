"""
Emails and etc
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import common
import secret

EMAIL = True

def email(subject, body, to=None):
    if not common.is_server():
        subject = 'LOCAL: %s' % (subject,)

    print('email:')
    print('\tsubject: %s' % (subject,))
    print('\tbody: %s' % (body,))
    print('\tto: %s' % (to,))

    if not EMAIL:
        return

    username = secret.EMAIL['USERNAME']
    password = secret.EMAIL['PASSWORD']

    toaddrs = username if to is None else to
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(username, password)
    server.sendmail(username, toaddrs, msg.as_string())
    server.quit()