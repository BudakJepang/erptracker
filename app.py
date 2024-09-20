from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from functools import wraps
from flask_mysqldb import MySQL
from flask import Flask, Blueprint
from modules.auth import auth_blueprint
from modules.user import user_blueprint
from modules.entity import entity_blueprint
from modules.pr import pr_blueprint
from modules.prf import prf_blueprint
from modules.vendor import vendor_blueprint
from modules.woc import woc_blueprint
import pandas as pd
from itsdangerous import URLSafeSerializer
import os
from datetime import timedelta
import jwt
from modules.helper import login_required

# ================================================================================================================
# MYSQL CONNNECTION SETUP PARAMETER 
# ================================================================================================================
def appFlask():
    app = Flask(__name__)

    # DB CONN MY MAC_________________________________________
    # app.config['MYSQL_HOST'] = '10.0.13.247' 
    # app.config['MYSQL_USER'] = 'rohman'
    # app.config['MYSQL_PASSWORD'] = '!@#Bismillah'
    # app.config['MYSQL_DB'] = 'playground'

    # DB ONPREM_______________________________________________
    # app.config['MYSQL_HOST'] = '10.0.12.53' 
    # app.config['MYSQL_USER'] = 'data-tech'
    # app.config['MYSQL_PASSWORD'] = '!@#Bismill4h'
    # app.config['MYSQL_DB'] = 'erp'

    # DB HOME_________________________________________________
    app.config['MYSQL_HOST'] = '10.1.1.11'
    app.config['MYSQL_USER'] = 'rohman'
    app.config['MYSQL_PASSWORD'] = '!@#Bismillah'
    app.config['MYSQL_DB'] = 'playground'

    # app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1)
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['ENTITY_UPLOAD_FOLDER'] = 'static/entity_logo'
    app.config['MAX_CONTENT_PATH'] = 16 * 1024 * 1024  # 16 MB max file size
    app.secret_key = 'prd'
    # SECRET_KEY=os.getenv('SECRET_KEY', 'your_secret_key')

    # GOOGLE SSO OAUTH2 CONFIG
    app.secret_key = "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"

    # JWT CONFIG
    app.config['JWT_SECRET_KEY'] = '!@#Bismill4h' # jwt key
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=30) #end session in 30 minutes
    jwt = JWTManager(app)
    return app

def mysqlConn(app):
    mysql = MySQL(app)
    return mysql

app = appFlask()
# jwt = JWTManager(app)
mysql = mysqlConn(app)
# ================================================================================================================


# ================================================================================================================
# MENU FILTER FOR USER AND LOGIN REQUIRED 
# ================================================================================================================

# FILTER USER BY MENU
def get_menu_data(user_id):

    # tambahkan route untuk module menu baru berdasarkan id_menu di db
    menu_url = {
        1: 'user.user_list',
        3: 'entity.entity_list',
        4: 'pr.pr_list',
        5: 'prf.prf_list',
        6: 'woc.woc_list',
        7: 'vendor.vendor_list',
    }

    # tambahkan icon untuk module menu baru berdasarkan id_menu di db
    menu_icon = {
        1: 'nav-icon far fa-user',
        3: 'nav-icon far fa-building',
        4: 'nav-icon far fa-edit',
        5: 'nav-icon far fa-edit',
        6: 'nav-icon far fa-edit',
        7: 'nav-icon far fa-handshake',
    }

    cursor = mysql.connection.cursor()
    cursor.execute('''
        SELECT 
        cat.id, cat.category_name,
        m.menu_name,
        m.id as menu_id
        FROM category_menu as cat
        LEFT JOIN menu AS m on cat.id = m.id_category
        LEFT JOIN user_access AS au on m.id = au.id_menu 
        WHERE au.id_user = %s
    ''', (user_id,))
    data = cursor.fetchall()
    cursor.close()

    menu_data = {}

    # looping untuk mendapatkan semua data yang didapat dari query db
    for row in data:

        # tampung hasil looping di variable
        category_id = row[0]
        category_name = row[1]
        item_name = row[2]
        menu_id = row[3]

        # kondisi untuk data menu yang kosong
        if category_name not in menu_data:
            menu_data[category_name] = []

        # kondisi untuk category name yang terdaftar di DB 
        if item_name:
            url = menu_url.get(menu_id)
            icon = menu_icon.get(menu_id)
            if url and icon:  # Pastikan url tidak None
                menu_data[category_name].append({
                    'name': item_name,
                    'url': url,
                    'icon': icon
                })
            else:
                print(f"Warning: No URL found for menu_id {menu_id}")

    return menu_data


# AUTHORIZE MENU ACCESS
# @app.context_processor
def inject_menu_data():
    if 'id' in session:
        menu_data = get_menu_data(session['id'])
    else:
        menu_data = {}
    return dict(menu_data=menu_data)


# ================================================================================================================
# ENCRYPTION SETUP
# ================================================================================================================
serializer = URLSafeSerializer(app.config['SECRET_KEY'])
def encrypt_id(user_id):
    s = URLSafeSerializer(app.config['SECRET_KEY'])
    return s.dumps(user_id)

def decrypt_id(token):
    try:
        return serializer.loads(token)
    except Exception as e:
        print(f"Decryption failed: {e}") 
        return None

@app.context_processor
def utility_processor():
    context = {}
    context['serializer'] = serializer
    context['encrypt_id'] = encrypt_id
    context['decrypt_id'] = decrypt_id
    context['menu_data'] = get_menu_data(session.get('id', 0))
    context['enumerate'] = enumerate
    return context
# ================================================================================================================


# ================================================================================================================
# ALL FUNCTION ROUTE
# ================================================================================================================
app.register_blueprint(auth_blueprint)
app.register_blueprint(user_blueprint)
app.register_blueprint(entity_blueprint)
app.register_blueprint(pr_blueprint)
app.register_blueprint(prf_blueprint)
app.register_blueprint(vendor_blueprint)
app.register_blueprint(woc_blueprint)

@app.route('/')
@login_required
# @jwt_required()
def index():
    return render_template('home.html')

# @app.route('/')
# @login_required
# @jwt_required()
# def index():
#     current_user = get_jwt_identity()  # Mendapatkan user yang login
#     return render_template('home.html', user=current_user)
# ================================================================================================================ 


# ================================================================================================================
# MAIN EXECUTION
# ================================================================================================================
if __name__ == '__main__':
    
    # MY HOME________________________________________
    # app.run(host='10.1.1.11', port=5000, debug=True)
    
    # MY MAC__________________________________________
    # app.run(host='10.0.13.247', port=5000, debug=True)
    app.run(host='0.0.0.0', port=80, debug=True)

    # ON PREM_________________________________________
    # app.run(host='10.0.13.53', port=5000, debug=True)
   
    # ON PREM DEV_____________________________________
    # app.run(host='10.0.12.53', port=1213, debug=True)

# ================================================================================================================