import json
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta

# SEND MAIL FOR NEW PR
def pr_mail(no_pr, email, requestName, approvalName, budget, dueDate, entityName):
    mail_user = "mohammad.nurohman@byorange.co.id"
    mail_pass = "hahu fbvj uxls njos"
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
    mail_user = "mohammad.nurohman@byorange.co.id"
    mail_pass = "hahu fbvj uxls njos"

    
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