import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

algo_mail_user = 'data-report@algo.co.id'
algo_mail_pass = 'nyoz rryz scsy srng'
bri_mail_recipients = 'rohmankpai@gmail.com'
startDate = '2024-07-22'

def invoice_mail(df, today, algo_mail_user, algo_mail_pass, bri_mail_recipients):
    invoice_date = today.replace("-", "/")
    sum_amount = df['grand_total'].sum()
    invoice_amount = '{:,.2f}'.format(float(sum_amount))
    invoice_amount = invoice_amount.replace('"', "")
    
    # Convert DataFrame to HTML table
    df_html = df.to_html(index=False, border=0, classes='dataframe', header=True)

    mailSender = algo_mail_user
    mailPass = algo_mail_pass
    mailRecipient = bri_mail_recipients
    msg = MIMEMultipart()
    msg['From'] = mailSender
    msg['To'] = mailRecipient
    msg['Subject'] = f"Algo e-Payment Receipt"

    html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: "Trebuchet MS", sans-serif;
                    font-size: 16px;
                }}
                p {{
                    font-family: "Trebuchet MS", serif;
                    font-size: 16px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    padding: 10px;
                    border: 1px solid black;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
                .container {{
                    border: 1px solid #000;
                    padding: 20px;
                    max-width: 800px;
                    margin: 0 auto;
                }}
                .logo {{
                    width: 200px;
                    display: block;
                    padding-bottom: 20px;
                }}
                .content {{
                    margin-top: 20px;
                }}
                .line {{
                    border-top: 1px solid #000;
                    margin-top: 10px;
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
        <p> Berikut adalah list refund </p>
        {df_html}
        <p> Data ini telah kami upload ke SFTP dengan nama berikut Refund_Transaction
            <br>
            Thank you \n 
            <br>
            Best Regards \n 
            <br> \n \n
            Algo Tech </p>
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
    server.sendmail(mailSender, mailRecipient, text)
    server.quit()

# Example usage
df = pd.DataFrame({
    'transaction_datetime': ['2024-07-02 13:01:13+00:00', '2024-07-02 03:16:22+00:00'],
    'transaction_created_datetime_utc7': ['2024-07-02 20:01:13+00:00', '2024-07-02 10:16:22+00:00'],
    'transaction_updated_datetime': ['2024-07-02 13:01:29+00:00', '2024-07-02 03:16:22+00:00'],
    'transaction_updated_datetime_utc7': ['2024-07-02 20:01:29+00:00', '2024-07-02 10:16:22+00:00'],
    'order_no': ['1808123748932120576', '1807976570628849664'],
    'customer_name': ['MUHAMMAD RIZQI ABYAN', 'MUHAMMAD RIZQI ABYAN'],
    'merchant_order_no': ['17199252697049', '17198901799579'],
    'settlement_code': ['20240702-NCsND', '20240702-rVtB-'],
    'partner_reference_no': ['240702200112', '240702101621'],
    'grand_total': [38900.0, 46500.0],
    'bri_fee': [259.2, 320.0],
    'algo_fee': [324.0, 400.0],
    'settlement_amount': [38640.8, 46180.0],
    'store_code': ['KD09', 'KD09'],
    'delivery_date': [pd.NaT, pd.NaT],
    'delivery_date_datetime_utc7': [pd.NaT, pd.NaT],
    'payment_method': ['Billing Payment', 'Billing Payment'],
    'last_created': ['2024-07-18 13:45:08.358145+00:00', '2024-07-18 13:45:08.3']
})

invoice_mail(df, startDate, algo_mail_user, algo_mail_pass, bri_mail_recipients)