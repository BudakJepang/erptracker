import json
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
import pytz
# from app import mysql
from flask_mysqldb import MySQL, MySQLdb


# SEND MAIL FOR NEW PR
def pr_mail(no_pr, email, requestName, approvalName, budget, dueDate, entityName):
    mail_user = "data-report@virgoku.id"
    mail_pass = "yistkgqarqncsims"
    # base trx date
    # date_object = datetime.strptime(startDate, "%Y-%m-%d")

    # change string format for mail invoice
    # trx_date = date_object.strftime("%Y-%B-%d")

    # subtract nextday for due date base on transantion date
    # next_day = date_object + timedelta(days=1)
    # dueDate = next_day.strftime("%Y-%B-%d")
    
    # preparing data for invoice amount
    # invoice_date = today.replace("-","/")
    # df['settlement_amount'] = df['settlement_amount'].astype(float).round(2)
    # sum_amount = df['settlement_amount'].sum()
    # invoice_amount = '{:,.2f}'.format(float(sum_amount))
    # invoice_amount = invoice_amount.replace('"',"")
    
    # sending mail
    approval  = 'rohmankpai@gmail.com, rohmankpai@gmail.com'
    mailSender = mail_user
    mailPass = mail_pass
    # mailRecipient = 'rohmankpai@gmail.com, rohmankpai@gmail.com'
    mailRecipient = email
    msg = MIMEMultipart()
    msg['From'] = mailSender
    msg['To'] = mailRecipient
    msg['Subject'] = f"PR Form Notification"

    html = """
        <html>
        <head>
            <style>
                body {
                    font-family: "Trebuchet MS", sans-serif;
                    font-size: 16px;
                }
                p {
                    font-family: "Trebuchet MS", serif;
                    font-size: 16px;
                }
                table td {
                    font-family: "Lucida Console", Courier, monospace;
                    font-size: 16px;
                }
                .container {
                    border: 1px solid #000;
                    padding: 20px;
                    max-width: 600px;
                    margin: 0 auto;
                }
                .logo {
                    width: 200px;
                    display: block;
                    /* margin: 0 auto; */
                    padding-bottom: 20px;
                }
                .content {
                    margin-top: 20px;
                }
                .line {
                    border-top: 1px solid #000;
                    margin-top: 10px;
                    margin-bottom: 10px;
                }
                table {
                    width: 20%;
                    border-collapse: collapse;
                }
                table td {
                    padding: 10px 10px;
                }
                table td.label {
                    text-align: left;
                    font-weight: bold;
                    width: 0%;
                }
                table td.value {
                    text-align: left;
                    font-weight: bold;
                    width: 0%;
                }
                th, td {
                    border-style: none;
                    font-weight: bold;
                    background-color: #f8f8f8;
                    text-align: center;
                }
                .table2 td {
                    padding: 30px 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                # <img src="./entity_logo/oid.png" alt="Logo" class="logo">
                <span style="float: right; font-size: 17px;">"""+entityName+"""</span>
                <br>
                <div class="content">
                    <p>Dear Mr/Mrs. """+approvalName+""",</p>
                    <p style="padding-bottom: 12px;">We would like to remind you that the following PR Number requires your approval, the PR details are as follows. Please approve it before the due date passes:</p>
                    <!-- <br> -->
                    <hr class="line">
                    <table class="table" style="width:80%;">
                        <tr>
                        <td style="text-align: left;">Nomor PR</td>
                        <td>:</td>
                        <td style="text-align: left;">IDR """+no_pr+"""</td>
                        </tr>
                        <tr>
                        <td style="text-align: left;">Budget Approve</td>
                        <td>:</td>
                        <td style="text-align: left;">"""+budget+"""</td>
                        </tr>
                        <tr>
                        <td style="text-align: left;">Due Date</td>
                        <td>:</td>
                        <td style="text-align: left;">"""+dueDate+"""</td>
                        </tr>
                    </table>
                    <hr class="line">
                    <br>
                    <table class="table2" style="width:100%">
                        <tr>
                            <td>Please provide information if the PR number is not approved
                            <br>
                            <br> PT. ORANGE INOVASI DIGITAL.</td>
                        </tr>
                    </table>
                    <br>
                    <p>Thank You</p>
                    <p>Best Regards</p>
                    <p>"""+requestName+"""</p>
                </div>
            </div>
        </body>
        </html>
    """

    body = MIMEText(html, 'html')
    msg.attach(body)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.connect("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(mailSender, mailPass)
    text = msg.as_string()
    server.sendmail(mailSender, approval.split(','), text)
    server.quit()
    result = "Sent"
    return result

def approval_notification_mail(email, no_pr):
    mail_user = "data-report@virgoku.id"
    mail_pass = "yistkgqarqncsims"

    
    # sending mail
    email  = 'rohmankpai@gmail.com, rohmankpai@gmail.com'
    mailSender = mail_user
    mailPass = mail_pass
    mailRecipient = email
    msg = MIMEMultipart()
    msg['From'] = mailSender
    msg['To'] = mailRecipient
    msg['Subject'] = f"PR Form Notification"

    html = """
        <html>
        <head>
            <style>
                body {
                    font-family: "Trebuchet MS", sans-serif;
                    font-size: 16px;
                }
                p {
                    font-family: "Trebuchet MS", serif;
                    font-size: 16px;
                }
                table td {
                    font-family: "Lucida Console", Courier, monospace;
                    font-size: 16px;
                }
                .container {
                    border: 1px solid #000;
                    padding: 20px;
                    max-width: 600px;
                    margin: 0 auto;
                }
                .logo {
                    width: 200px;
                    display: block;
                    /* margin: 0 auto; */
                    padding-bottom: 20px;
                }
                .content {
                    margin-top: 20px;
                }
                .line {
                    border-top: 1px solid #000;
                    margin-top: 10px;
                    margin-bottom: 10px;
                }
                table {
                    width: 20%;
                    border-collapse: collapse;
                }
                table td {
                    padding: 10px 10px;
                }
                table td.label {
                    text-align: left;
                    font-weight: bold;
                    width: 0%;
                }
                table td.value {
                    text-align: left;
                    font-weight: bold;
                    width: 0%;
                }
                th, td {
                    border-style: none;
                    font-weight: bold;
                    background-color: #f8f8f8;
                    text-align: center;
                }
                .table2 td {
                    padding: 30px 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <img src="./entity_logo/oid.png" alt="Logo" class="logo">
                <span style="float: right; font-size: 17px;">Date: """+startDate+"""</span>
                <br>
                <div class="content">
                    <p>Dear Mr/Mrs.,</p>
                    <p style="padding-bottom: 12px;">We would like to remind you that the following PR Number requires your approval, the PR details are as follows. Please approve it before the due date passes:</p>
                    <!-- <br> -->
                    <hr class="line">
                    <table class="table" style="width:80%;">
                        <tr>
                        <td style="text-align: left;">Nomor PR</td>
                        <td>:</td>
                        <td style="text-align: left;">IDR """+no_pr+"""</td>
                        </tr>
                        <tr>
                        <td style="text-align: left;">Budget Approve</td>
                        <td>:</td>
                        <td style="text-align: left;">"""+total_budget_approved+""" (UTC+7)</td>
                        </tr>
                        <tr>
                        <td style="text-align: left;">Due Date</td>
                        <td>:</td>
                        <td style="text-align: left;">"""+today+""" (UTC+7)</td>
                        </tr>
                    </table>
                    <hr class="line">
                    <br>
                    <table class="table2" style="width:100%">
                        <tr>
                            <td>Please provide information if the PR number is not approved
                            <br>
                            <br> PT. ORANGE INOVASI DIGITAL.</td>
                        </tr>
                    </table>
                    <br>
                    <p>Thank You</p>
                </div>
            </div>
        </body>
        </html>
    """

    body = MIMEText(html, 'html')
    msg.attach(body)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.connect("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(mailSender, mailPass)
    text = msg.as_string()
    server.sendmail(mailSender, mailRecipient.split(','), text)
    server.quit()
    result = "Sent"
    return result

def alert_mail(no_pr, mail_recipient, nama_project, nama_entity, nama_requester, tanggal_request, budget, due_date, approval_name, today):
    mail_user = "data-report@virgoku.id"
    mail_pass = "yistkgqarqncsims"

    due_date = str(due_date)
    amount = '{:,.2f}'.format(float(budget))
    mailSender = mail_user
    mailPass = mail_pass
    mailRecipient = mail_recipient
    msg = MIMEMultipart()
    msg['From'] = mailSender
    msg['To'] = mailRecipient
    msg['Subject'] = f"PR Form Notification"

    html = """
        <html>
        <head>
            <style>
                body {
                    font-family: "Trebuchet MS", sans-serif;
                    font-size: 16px;
                }
                p {
                    font-family: "Trebuchet MS", serif;
                    font-size: 16px;
                }
                table td {
                    font-family: "Lucida Console", Courier, monospace;
                    font-size: 16px;
                }
                .container {
                    border: 1px solid #000;
                    padding: 20px;
                    max-width: 600px;
                    margin: 0 auto;
                }
                .logo {
                    width: 200px;
                    display: block;
                    /* margin: 0 auto; */
                    padding-bottom: 20px;
                }
                .content {
                    margin-top: 20px;
                }
                .line {
                    border-top: 1px solid #000;
                    margin-top: 10px;
                    margin-bottom: 10px;
                }
                table {
                    width: 20%;
                    border-collapse: collapse;
                }
                table td {
                    padding: 10px 10px;
                }
                table td.label {
                    text-align: left;
                    font-weight: bold;
                    width: 0%;
                }
                table td.value {
                    text-align: left;
                    font-weight: bold;
                    width: 0%;
                }
                th, td {
                    border-style: none;
                    font-weight: bold;
                    background-color: #f8f8f8;
                    text-align: center;
                }
                .table2 td {
                    padding: 30px 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <img src="./entity_logo/oid.png" alt="Logo" class="logo">
                <span style="float: right; font-size: 17px;">Date: """+today+"""</span>
                <br>
                <div class="content">
                    <p>Dear Mr/Mrs.<strong> """+approval_name+"""</strong>,</p>
                    <p style="padding-bottom: 12px;">We would like to remind you that the following PR Number requires your approval, the PR details are as follows. Please approve it before the due date passes:</p>
                    <!-- <br> -->
                    <hr class="line">
                    <table class="table" style="width:100%;">
                        <tr>
                            <td style="text-align: left;">Nomor PR</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+no_pr+"""</td>
                        </tr>
                        <tr>
                            <td style="text-align: left;">Project Name</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+nama_project+"""</td>
                        </tr>
                        <tr>
                            <td style="text-align: left;">Entity Name</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+nama_entity+"""</td>
                        </tr>
                            <td style="text-align: left;">Budget Approved</td>
                            <td>:</td>
                            <td style="text-align: left;">IDR """+amount+"""</td>
                        </tr>
                        <tr>
                            <td style="text-align: left;">Due Date</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+due_date+"""</td>
                        </tr>
                    </table>
                    <hr class="line">
                    <br>
                    <table class="table2" style="width:100%">
                        <tr>
                            <td>Please follow this link below
                            <br>
                            <br> 
                            <a href="http://10.0.13.247:5000/pr_detail_page/"""+no_pr+""""">click here</a>
                        </tr>
                    </table>
                    <br>
                    <p>Best Regards,</p>
                    <p>"""+nama_requester+"""</p>
                    <p>Thank you</p>
                </div>
            </div>
        </body>
        </html>
    """

    body = MIMEText(html, 'html')
    msg.attach(body)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.connect("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(mailSender, mailPass)
    text = msg.as_string()
    server.sendmail(mailSender, mailRecipient.split(','), text)
    server.quit()
    result = "Sent"
    return result


def pr_alert_mail(no_pr, mail_recipient):
    mail_user = "data-report@virgoku.id"
    mail_pass = "yistkgqarqncsims"

    # due_date = str(due_date)
    # amount = '{:,.2f}'.format(float(budget))
    mailSender = mail_user
    mailPass = mail_pass
    mailRecipient = mail_recipient
    msg = MIMEMultipart()
    msg['From'] = mailSender
    msg['To'] = mailRecipient
    msg['Subject'] = f"PR Form Notification"

    html = """
        <html>
        <head>
            <style>
                body {
                    font-family: "Trebuchet MS", sans-serif;
                    font-size: 16px;
                }
                p {
                    font-family: "Trebuchet MS", serif;
                    font-size: 16px;
                }
                table td {
                    font-family: "Lucida Console", Courier, monospace;
                    font-size: 16px;
                }
                .container {
                    border: 1px solid #000;
                    padding: 20px;
                    max-width: 600px;
                    margin: 0 auto;
                }
                .logo {
                    width: 200px;
                    display: block;
                    /* margin: 0 auto; */
                    padding-bottom: 20px;
                }
                .content {
                    margin-top: 20px;
                }
                .line {
                    border-top: 1px solid #000;
                    margin-top: 10px;
                    margin-bottom: 10px;
                }
                table {
                    width: 20%;
                    border-collapse: collapse;
                }
                table td {
                    padding: 10px 10px;
                }
                table td.label {
                    text-align: left;
                    font-weight: bold;
                    width: 0%;
                }
                table td.value {
                    text-align: left;
                    font-weight: bold;
                    width: 0%;
                }
                th, td {
                    border-style: none;
                    font-weight: bold;
                    background-color: #f8f8f8;
                    text-align: center;
                }
                .table2 td {
                    padding: 30px 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <img src="./entity_logo/oid.png" alt="Logo" class="logo">
                <span style="float: right; font-size: 17px;">Date: """+no_pr+"""</span>
                <br>
                <div class="content">
                    <p>Dear Mr/Mrs.<strong> """+no_pr+"""</strong>,</p>
                    <p style="padding-bottom: 12px;">We would like to remind you that the following PR Number requires your approval, the PR details are as follows. Please approve it before the due date passes:</p>
                    <!-- <br> -->
                    <hr class="line">
                    <table class="table" style="width:100%;">
                        <tr>
                            <td style="text-align: left;">Nomor PR</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+no_pr+"""</td>
                        </tr>
                        <tr>
                            <td style="text-align: left;">Project Name</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+no_pr+"""</td>
                        </tr>
                        <tr>
                            <td style="text-align: left;">Entity Name</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+no_pr+"""</td>
                        </tr>
                            <td style="text-align: left;">Budget Approved</td>
                            <td>:</td>
                            <td style="text-align: left;">IDR """+no_pr+"""</td>
                        </tr>
                        <tr>
                            <td style="text-align: left;">Due Date</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+no_pr+"""</td>
                        </tr>
                    </table>
                    <hr class="line">
                    <br>
                    <table class="table2" style="width:100%">
                        <tr>
                            <td>Please follow this link below
                            <br>
                            <br> 
                            <a href="http://10.0.13.247:5000/pr_detail_page/"""+no_pr+""""">click here</a>
                        </tr>
                    </table>
                    <br>
                    <p>Best Regards,</p>
                    <p>""""""</p>
                    <p>Thank you</p>
                </div>
            </div>
        </body>
        </html>
    """

    body = MIMEText(html, 'html')
    msg.attach(body)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.connect("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(mailSender, mailPass)
    text = msg.as_string()
    server.sendmail(mailSender, mailRecipient.split(','), text)
    server.quit()
    result = "Sent"
    return result


# MULTIPLE SENT MAIL________________________________________________________________
# cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
# query_mail = '''
# SELECT 
#     no_pr,
#     approval_user_id,
#     ua.username,
#     ua.email 
# FROM pr_approval pa 
# LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
# WHERE no_pr = %s
# '''
# cur.execute(query_mail, [no_pr])
# data_email = cur.fetchall()
# cur.close()

# emails = [row['email'] for row in data_email if row['email']]
# email_list = ', '.join(emails)
# pr_alert_mail(no_pr, email_list)


# SINGLE TO FIRST APPROVAL SENT MAIL________________________________________________________________
def send_approval_mail(no_pr):
    from app import mysql
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query_single_mail = '''
        SELECT 
            no_pr,
            approval_no,
            approval_user_id,
            ua.username,
            ua.email 
        FROM pr_approval pa 
        LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
        WHERE no_pr = %s
        ORDER BY 2 ASC
        LIMIT 1
    '''
    cur.execute(query_single_mail, [no_pr])
    first_approval_mail = cur.fetchone()

    mail_approval_recipient = first_approval_mail['email']
    pr_alert_mail(no_pr, mail_approval_recipient)

    cur.close()


# ========================================================================================================================================
# PRF MAIL UTILITY
# ========================================================================================================================================
def prf_alert_mail(no_prf, mail_recipient):
    mail_user = "data-report@virgoku.id"
    mail_pass = "yistkgqarqncsims"

    # due_date = str(due_date)
    # amount = '{:,.2f}'.format(float(budget))
    mailSender = mail_user
    mailPass = mail_pass
    mailRecipient = mail_recipient
    msg = MIMEMultipart()
    msg['From'] = mailSender
    msg['To'] = mailRecipient
    msg['Subject'] = f"PR Form Notification"

    html = """
        <html>
        <head>
            <style>
                body {
                    font-family: "Trebuchet MS", sans-serif;
                    font-size: 16px;
                }
                p {
                    font-family: "Trebuchet MS", serif;
                    font-size: 16px;
                }
                table td {
                    font-family: "Lucida Console", Courier, monospace;
                    font-size: 16px;
                }
                .container {
                    border: 1px solid #000;
                    padding: 20px;
                    max-width: 600px;
                    margin: 0 auto;
                }
                .logo {
                    width: 200px;
                    display: block;
                    /* margin: 0 auto; */
                    padding-bottom: 20px;
                }
                .content {
                    margin-top: 20px;
                }
                .line {
                    border-top: 1px solid #000;
                    margin-top: 10px;
                    margin-bottom: 10px;
                }
                table {
                    width: 20%;
                    border-collapse: collapse;
                }
                table td {
                    padding: 10px 10px;
                }
                table td.label {
                    text-align: left;
                    font-weight: bold;
                    width: 0%;
                }
                table td.value {
                    text-align: left;
                    font-weight: bold;
                    width: 0%;
                }
                th, td {
                    border-style: none;
                    font-weight: bold;
                    background-color: #f8f8f8;
                    text-align: center;
                }
                .table2 td {
                    padding: 30px 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <img src="./entity_logo/oid.png" alt="Logo" class="logo">
                <span style="float: right; font-size: 17px;">Date: """+no_prf+"""</span>
                <br>
                <div class="content">
                    <p>Dear Mr/Mrs.<strong> """+no_prf+"""</strong>,</p>
                    <p style="padding-bottom: 12px;">We would like to remind you that the following PR Number requires your approval, the PR details are as follows. Please approve it before the due date passes:</p>
                    <!-- <br> -->
                    <hr class="line">
                    <table class="table" style="width:100%;">
                        <tr>
                            <td style="text-align: left;">Nomor PR</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+no_prf+"""</td>
                        </tr>
                        <tr>
                            <td style="text-align: left;">Project Name</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+no_prf+"""</td>
                        </tr>
                        <tr>
                            <td style="text-align: left;">Entity Name</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+no_prf+"""</td>
                        </tr>
                            <td style="text-align: left;">Budget Approved</td>
                            <td>:</td>
                            <td style="text-align: left;">IDR """+no_prf+"""</td>
                        </tr>
                        <tr>
                            <td style="text-align: left;">Due Date</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+no_prf+"""</td>
                        </tr>
                    </table>
                    <hr class="line">
                    <br>
                    <table class="table2" style="width:100%">
                        <tr>
                            <td>Please follow this link below
                            <br>
                            <br> 
                            <a href="http://10.0.13.247:5000/pr_detail_page/"""+no_prf+""""">click here</a>
                        </tr>
                    </table>
                    <br>
                    <p>Best Regards,</p>
                    <p>""""""</p>
                    <p>Thank you</p>
                </div>
            </div>
        </body>
        </html>
    """

    body = MIMEText(html, 'html')
    msg.attach(body)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.connect("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(mailSender, mailPass)
    text = msg.as_string()
    server.sendmail(mailSender, mailRecipient.split(','), text)
    server.quit()
    result = "Sent"
    return result

def prf_send_approval_manual(no_prf, mail_recipient, vendor_name, department, nama_entity, nama_requester, tanggal_request, budget, approval_name, today):
    mail_user = "data-report@virgoku.id"
    mail_pass = "yistkgqarqncsims"

    tanggal_request = str(tanggal_request)
    amount = '{:,.2f}'.format(float(budget))
    mailSender = mail_user
    mailPass = mail_pass
    mailRecipient = mail_recipient
    msg = MIMEMultipart()
    msg['From'] = mailSender
    msg['To'] = mailRecipient
    msg['Subject'] = f"PR Form Notification"

    html = """
        <html>
        <head>
            <style>
                body {
                    font-family: "Trebuchet MS", sans-serif;
                    font-size: 16px;
                }
                p {
                    font-family: "Trebuchet MS", serif;
                    font-size: 16px;
                }
                table td {
                    font-family: "Lucida Console", Courier, monospace;
                    font-size: 16px;
                }
                .container {
                    border: 1px solid #000;
                    padding: 20px;
                    max-width: 600px;
                    margin: 0 auto;
                }
                .logo {
                    width: 200px;
                    display: block;
                    /* margin: 0 auto; */
                    padding-bottom: 20px;
                }
                .content {
                    margin-top: 20px;
                }
                .line {
                    border-top: 1px solid #000;
                    margin-top: 10px;
                    margin-bottom: 10px;
                }
                table {
                    width: 20%;
                    border-collapse: collapse;
                }
                table td {
                    padding: 10px 10px;
                }
                table td.label {
                    text-align: left;
                    font-weight: bold;
                    width: 0%;
                }
                table td.value {
                    text-align: left;
                    font-weight: bold;
                    width: 0%;
                }
                th, td {
                    border-style: none;
                    font-weight: bold;
                    background-color: #f8f8f8;
                    text-align: center;
                }
                .table2 td {
                    padding: 30px 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>
                  <large>"""+nama_entity+"""</large>
                </h4>
                <span style="float: right; font-size: 17px;">Date: """+today+"""</span>
                <br>
                <div class="content">
                    <p>Dear Mr/Mrs.<strong> """+approval_name+"""</strong>,</p>
                    <p style="padding-bottom: 12px;">We would like to remind you that the following PRF Number requires your approval, the PRF details are as follows. Please approve it before the due date passes:</p>
                    <!-- <br> -->
                    <hr class="line">
                    <table class="table" style="width:100%;">
                        <tr>
                            <td style="text-align: left;">Nomor PRF</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+no_prf+"""</td>
                        </tr>
                        <tr>
                            <td style="text-align: left;">Vendor Name</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+vendor_name+"""</td>
                        </tr>
                        <tr>
                            <td style="text-align: left;">Department</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+department+"""</td>
                        </tr>
                        <tr>
                            <td style="text-align: left;">Amount</td>
                            <td>:</td>
                            <td style="text-align: left;">IDR """+amount+"""</td>
                        </tr>
                        <tr>
                            <td style="text-align: left;">Request Date</td>
                            <td>:</td>
                            <td style="text-align: left;">"""+tanggal_request+"""</td>
                        </tr>
                    </table>
                    <hr class="line">
                    <br>
                    <table class="table2" style="width:100%">
                        <tr>
                            <td>Please follow this link below
                            <br>
                            <br> 
                            <a href="http://10.0.13.247:5000/prf_detail/"""+no_prf+""""">click here</a>
                        </tr>
                    </table>
                    <br>
                    <p>Best Regards,</p>
                    <p>"""+nama_requester+"""</p>
                    <p>Thank you</p>
                </div>
            </div>
        </body>
        </html>
    """

    body = MIMEText(html, 'html')
    msg.attach(body)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.connect("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(mailSender, mailPass)
    text = msg.as_string()
    server.sendmail(mailSender, mailRecipient.split(','), text)
    server.quit()
    result = "Sent"
    return result