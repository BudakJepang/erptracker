from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from functools import wraps
from flask_mysqldb import MySQL
from flask import Flask, Blueprint
from modules.auth import auth_blueprint
from modules.user import user_blueprint
from modules.entity import entity_blueprint
from modules.pr import pr_blueprint
import pandas as pd


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
    app.config['MYSQL_HOST'] = '10.0.12.53' 
    app.config['MYSQL_USER'] = 'data-tech'
    app.config['MYSQL_PASSWORD'] = '!@#Bismill4h'
    app.config['MYSQL_DB'] = 'erp'

    # DB HOME_________________________________________________
    # app.config['MYSQL_HOST'] = '10.1.1.6'
    # app.config['MYSQL_USER'] = 'rohman'
    # app.config['MYSQL_PASSWORD'] = '!@#Bismillah'
    # app.config['MYSQL_DB'] = 'playground'

    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_PATH'] = 16 * 1024 * 1024  # 16 MB max file size
    app.secret_key = 'prd'
    return app

def mysqlConn(app):
    mysql = MySQL(app)
    return mysql

app = appFlask()
mysql = mysqlConn(app)
# ================================================================================================================


# ================================================================================================================
# MENU FILTER FOR USER AND LOGIN REQUIRED 
# ================================================================================================================
# LOCK REQUIRED TO LOGIN
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('auth.auth'))
        return f(*args, **kwargs)
    return decorated_function


# FILTER USER BY MENU
def get_menu_data(user_id):

    # tambahkan route untuk module menu baru berdasarkan id_menu di db
    menu_url = {
        1: 'user.user_list',
        3: 'entity.entity_list',
        4: 'pr.pr_list'
    }

    # tambahkan icon untuk module menu baru berdasarkan id_menu di db
    menu_icon = {
        1: 'nav-icon far fa-user',
        3: 'nav-icon far fa-building',
        4: 'nav-icon far fa-edit'
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
@app.context_processor
def inject_menu_data():
    if 'id' in session:
        menu_data = get_menu_data(session['id'])
    else:
        menu_data = {}
    return dict(menu_data=menu_data)

@app.context_processor
def utility_processor():
    return dict(enumerate=enumerate)


def check_access(menu_id):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('id')
            if not user_id:
                return redirect(url_for('login'))

            cursor = mysql.connection.cursor()
            cursor.execute('SELECT 1 FROM user_access WHERE user_id = %s AND menu_id = %s', (user_id, menu_id))
            access = cursor.fetchone()
            cursor.close()

            if not access:
                flash('You do not have access to this page', 'danger')
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
# ================================================================================================================


# ================================================================================================================
# ALL FUNCTION ROUTE
# ================================================================================================================
app.register_blueprint(auth_blueprint)
app.register_blueprint(user_blueprint)
app.register_blueprint(entity_blueprint)
app.register_blueprint(pr_blueprint)

@app.route('/')
@login_required
def index():
    return render_template('home.html')
# ================================================================================================================ 


# ================================================================================================================
# MAIN EXECUTION
# ================================================================================================================
if __name__ == '__main__':
    
    # MY HOME________________________________________
    app.run(host='10.1.1.6', port=5000, debug=True)
    
    # MY MAC__________________________________________
    # app.run(host='10.0.13.247', port=5000, debug=True)

    # ON PREM_________________________________________
    # app.run(host='10.0.13.53', port=5000, debug=True)

# ================================================================================================================