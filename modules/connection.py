from flask import Flask
from flask_mysqldb import MySQL

# ================================================================================================================
# MYSQL CONNNECTION SETUP PARAMETER 
# ================================================================================================================
def appFlask():
    app = Flask(__name__)
    # app.config['MYSQL_HOST'] = '10.0.13.247'
    # app.config['MYSQL_HOST'] = '10.1.1.19'
    app.config['MYSQL_HOST'] = '10.1.1.9'
    # app.config['MYSQL_USER'] = 'popey'
    app.config['MYSQL_USER'] = 'rohman'
    app.config['MYSQL_PASSWORD'] = '!@#Bismillah'
    # app.config['MYSQL_PASSWORD'] = 'Kpaii1234'
    app.config['MYSQL_DB'] = 'playground'
    app.secret_key = 'testing'
    return app

def mysqlConn(app):
    mysql = MySQL(app)
    return mysql

app = appFlask()
mysql = mysqlConn(app)
# ================================================================================================================
# ================================================================================================================