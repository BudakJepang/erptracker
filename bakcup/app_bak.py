from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import pytz
import random
import hashlib
# from modules.auth import auth_blueprint
# from modules.connection import mysqlConn
# from modules.home import home_blueprint
# from modules.user import user_blueprint

def hash_id(user_id):
    return hashlib.sha256(str(user_id).encode()).hexdigest()

def convert_time_to_wib(dtobject):
    tz = pytz.timezone('Asia/Jakarta')
    utc = pytz.timezone('UTC')
    tz_aware = utc.localize(dtobject)
    localtime = tz_aware.astimezone(tz)
    return localtime


# ORIGINAL GET MENU
# def get_menu_data(user_id):
#     cursor = mysql.connection.cursor()
#     cursor.execute('''
#         SELECT 
#         cat.id, cat.category_name,
#         m.menu_name,
#         m.id as menu_id -- Tambahkan menu_id
#         FROM category_menu as cat
#         LEFT JOIN menu AS m on cat.id = m.id_category
#         LEFT JOIN access_users AS au on m.id = au.id_menu 
#         WHERE au.id_user = %s
#     ''', (user_id,))
#     data = cursor.fetchall()
#     cursor.close()

#     menu_data = {}
#     for row in data:
#         category_id = row[0]
#         category_name = row[1]
#         item_name = row[2]
#         menu_id = row[3]  # Ambil menu_id

#         if category_name not in menu_data:
#             menu_data[category_name] = []

#         if item_name:
#             menu_data[category_name].append({
#                 'name': item_name,
#                 'url': MENU_URLS.get(menu_id)  # Dapatkan URL dari dictionary
#             })

#     return menu_data

# mysql = mysqlConn(app)
# ================================================================================================================
# GLOBAL PARAMETER ===============================================================================================
# ================================================================================================================
# current_timestamp = convert_time_to_wib(datetime.now()).strftime("%Y-%m-%d %H%M%S")
current_timestamp = datetime.now()
app = Flask(__name__)
# app.config.update(
#     SESSION_COOKIE_SECURE=True,
#     SESSION_COOKIE_HTTPONLY=True,
# )
app.permanent_session_lifetime = timedelta(minutes=30)

# Register Blueprints
# app.register_blueprint(auth_blueprint)

# Register Blueprints
# app.register_blueprint(auth_blueprint)
# app.register_blueprint(home_blueprint)
# app.register_blueprint(user_blueprint)
# ================================================================================================================
# END GLOBAL PARAMETER ===========================================================================================
# ================================================================================================================

# ================================================================================================================
# MYSQL CONNNECTION SETUP PARAMETER ==============================================================================
# ================================================================================================================
app.secret_key = 'testing'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'popey'
app.config['MYSQL_PASSWORD'] = 'Kpaii1234'
app.config['MYSQL_DB'] = 'playground'
mysql = MySQL(app)
# ================================================================================================================
# END MYSQL CONNNECTION SETUP PARAMETER ==========================================================================
# ================================================================================================================


# ================================================================================================================
# LOGIN REQUIRED AND HOME INDEX ROUTE ============================================================================
# ================================================================================================================
# set session not permanent
@app.before_request
def make_session_permanent():
    session.permanent = False

# lock login validation
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    return decorated_function

# for send back to auth if login is failed
@app.route('/auth')
def auth():
    return render_template('auth/login.html')

def check_access(menu_id):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('id')
            if not user_id:
                return redirect(url_for('login'))

            cursor = mysql.connection.cursor()
            cursor.execute('SELECT 1 FROM access_users WHERE user_id = %s AND menu_id = %s', (user_id, menu_id))
            access = cursor.fetchone()
            cursor.close()

            if not access:
                flash('You do not have access to this page', 'danger')
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_menu_data(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute('''
        SELECT 
        cat.id, cat.category_name,
        m.menu_name 
        FROM category_menu as cat
        LEFT JOIN menu AS m on cat.id = m.id_category
        LEFT JOIN access_users AS au on m.id = au.menu_id 
        WHERE au.user_id = %s
    ''', (user_id,))
    data = cursor.fetchall()
    cursor.close()

    menu_data = {}
    for row in data:
        category_id = row[0]
        category_name = row[1]
        item_name = row[2]

        if category_name not in menu_data:
            menu_data[category_name] = []
        
        if item_name:
            menu_data[category_name].append(item_name)

    return menu_data

@app.context_processor
def inject_menu_data():
    if 'id' in session:
        menu_data = get_menu_data(session['id'])
    else:
        menu_data = {}
    return dict(menu_data=menu_data)

# mengambil kategori dari database
def get_categories():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, category_name FROM category_menu')
    categories = cursor.fetchall()
    cursor.close()
    return categories

# context global sehingga bisa diakses dari semua template
@app.context_processor
def inject_categories():
    categories = get_categories()
    return dict(categories=categories)

# index / home page
@app.route('/')
@login_required
def index():
    return render_template('home.html')
# ================================================================================================================
# END LOGIN REQUIRED AND HOME INDEX ROUTE ========================================================================
# ================================================================================================================


# ================================================================================================================
# AUTHENTICATION ROUTE ===========================================================================================
# ================================================================================================================
# login authentication mail and password
@app.route('/login', methods=('GET','POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # check users data
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id, username, email, password, level FROM user_accounts WHERE email=%s', (email,))
        account = cursor.fetchone()
        
        if account is None:
            flash('Login failed, please check your username', 'danger')
        elif not check_password_hash(account[3], password):
            flash('Login failed, check your password is correct', 'danger')
        else:
            session.clear()
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            session['level'] = account[4]
            return redirect(url_for('index'))
        
    return render_template('auth/login.html')

# logout
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    session.pop('level', None)
    return redirect(url_for('login'))
# ================================================================================================================
# END AUTHENTICATION ROUTE =======================================================================================
# ================================================================================================================



# ================================================================================================================
# USERS & REGISTER ROUTE =========================================================================================
# ================================================================================================================
# list user
@app.route('/user_list')
@login_required
@check_access(menu_id=1)
def user_list():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, username, email, level, created_at FROM user_accounts')
    users = cursor.fetchall()

    cursor.close()
    return render_template('users/user_list.html', users=users)


# registration and access user
@app.route('/register', methods=('GET','POST'))
@login_required
def register():
     if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        level = request.form['level']
        selected_menus = request.form.getlist('menus')  # ambil daftar menu yang dipilih dari view html

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT username, email FROM user_accounts WHERE username=%s OR email=%s', (username, email))
        account = cursor.fetchone()
        
        if account is None:
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO user_accounts (username, email, password, level, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (username, email, generate_password_hash(password), level, current_timestamp, current_timestamp))
            mysql.connection.commit()
            user_id = cursor.lastrowid  # get ID user yang baru saja dibuat

            # simpan data menu yang dipilih ke tabel access_users
            for menu_id in selected_menus:
                cursor.execute('''
                    INSERT INTO access_users (user_id, menu_id, created_at, updated_at)
                    VALUES (%s, %s, %s, %s)
                ''', (user_id, menu_id, current_timestamp, current_timestamp))
            
            mysql.connection.commit()
            cursor.close()
            flash('Registration Success', 'success')
            return redirect(url_for('user_list'))
        else:
            cursor.close()
            flash('Username or Email already exists', 'danger')
            return redirect(url_for('user_list'))
     return render_template('users/user_list.html')

# change password users not admin
@app.route('/user_change_password/<int:id>', methods=['GET', 'POST'])
@login_required
def user_change_password(id):
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        user_id = request.form['user_id']
        username = request.form['username']
        email = request.form['email']
        current_password = request.form['current_password']
        new_password = request.form['new_password']

        cursor.execute('SELECT password FROM user_accounts WHERE id=%s', (user_id,))
        user = cursor.fetchone()

        if user and check_password_hash(user[0], current_password):
            # checking password if current password is correct
            if new_password:
                new_password_hashed = generate_password_hash(new_password)
                cursor.execute('''
                    UPDATE user_accounts 
                    SET username=%s, email=%s, password=%s, updated_at=%s 
                    WHERE id=%s
                ''', (username, email, new_password_hashed, datetime.now(), user_id))
            else:
                cursor.execute('''
                    UPDATE user_accounts 
                    SET username=%s, email=%s, updated_at=%s 
                    WHERE id=%s
                ''', (username, email, datetime.now(), user_id))
            
            mysql.connection.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('user_list'))
        else:
            # Current password is incorrect
            flash('Current password is incorrect', 'danger')
            
        return redirect(url_for('user_change_password', id=user_id))
    
    cursor.execute('SELECT id, username, email, level FROM user_accounts WHERE id=%s', (id,))
    user = cursor.fetchone()
    cursor.close()

    if user is None:
        flash('User not found', 'danger')
        return redirect(url_for('list_users'))
    
    return render_template('users/user_change_password.html', user=user)

# user settings
@app.route('/user_settings')
@login_required
def user_settings():
    user_id = session.get('user_id')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, username FROM users_account WHERE id=%s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    
    return render_template('base.html', user=user)

# edit users admin
@app.route('/user_edit')
@login_required
def user_edit():
    return render_template('users/user_edit.html')

# delete user
@app.route('/delete_user/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM user_accounts WHERE id = %s', (id,))
    mysql.connection.commit()
    cursor.close()
    flash('User has been deleted successfully', 'success')
    return redirect(url_for('user_list'))

# ================================================================================================================
# END USERS ROUTE ================================================================================================
# ================================================================================================================

@app.route('/get_menus', methods=['GET'])
@login_required
def get_menus():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, menu_name FROM menu')
    menus = cursor.fetchall()
    cursor.close()
    return jsonify(menus)  # Kembalikan data dalam format JSON


# @app.route('/category_menu')
# @login_required
# def category_menu():
#     cursor = mysql.connection.cursor()
#     cursor.execute('SELECT id, category_name FROM category_menu')
#     categories = cursor.fetchall()
#     cursor.close()
#         # Logging for debugging
#     print("Categories fetched from database: ", categories)
#     return render_template('users/user_list.html', categories=categories)







# ================================================================================================================
# TESTING UNIQUE ID ==============================================================================================
# ================================================================================================================
# Generate Unique ID function based on entity_type and procurement_type
def generate_unique_id(entity_type, procurement_type):
    prefix = 'B/' if procurement_type == 'barang' else 'L/' if procurement_type == 'license' else ''
    return f"{prefix}{entity_type.upper()}/{random.randint(1, 999999):06}"

current_id = 1
def generate_unique_id_serial(entity_type, procurement_type):
    global current_id
    prefix = 'B/' if procurement_type == 'barang' else 'L/' if procurement_type == 'license' else ''
    formatted_id = f'{current_id:06}'
    current_id += 1
    return f"{prefix}{entity_type.upper()}/{formatted_id}"

# Route for inserting procure data
@app.route('/insert_procure', methods=['GET', 'POST'])
def insert_procure():
    if request.method == 'POST':
        try:
            entity_type = request.form['entity_type']
            procurement_type = request.form['procurement_type']

            # Generate unique ID based on entity_type and procurement_type
            # unique_id = generate_unique_id(entity_type, procurement_type)
            unique_id = generate_unique_id_serial(entity_type, procurement_type)
            print(unique_id)
            
            # Print the SQL query and parameters
            query = 'INSERT INTO procure_test (id) VALUES (%s)'
            print(f"Executing query: {query} with parameters: ({unique_id},)")

            # Insert into MySQL
            cursor = mysql.connection.cursor()
            cursor.execute(query, (unique_id,))
            mysql.connection.commit()
            cursor.close()
            flash('Data inserted successfully', 'success')
            return redirect(url_for('insert_form'))

        except Exception as e:
            flash(f'Error inserting data: {str(e)}', 'danger')
            return redirect(url_for('insert_form'))

    return render_template('insert_form.html')

# Route for rendering insert form
@app.route('/insert_form')
def insert_form():
    return render_template('insert_form.html')
# ================================================================================================================
# END TESTING UNIQUE ID ==========================================================================================
# ================================================================================================================




if __name__ == '__main__':
    app.run(host='10.1.1.8', port=5000, debug=True)



# BACKUP ===========================================================================================================
# login backup
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']
        
#         cursor = mysql.connection.cursor()
#         cursor.execute('SELECT * FROM user_accounts WHERE email = %s', (email,))
#         account = cursor.fetchone()
#         cursor.close()
        
#         if account and check_password_hash(account[3], password):
#             flash('Login successful!', 'success')
#             return redirect(url_for('home')) 
#         else:
#             flash('Invalid email or password', 'danger')
#             return redirect(url_for('login'))
#     return render_template('auth/login.html')

# from flask import jsonify
# @app.route('/register', methods=('GET', 'POST'))
# def register():
#     if request.method == 'POST':
#         username = request.form['username']
#         email = request.form['email']
#         password = request.form['password']
#         level = request.form['level']
        
#         cursor = mysql.connection.cursor()
#         cursor.execute('SELECT * FROM user_accounts WHERE username=%s OR email=%s', (username, email))
#         account = cursor.fetchone()
        
#         if account is None:
#             current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#             cursor.execute('''
#                 INSERT INTO user_accounts (username, email, password, level, created_at, updated_at) 
#                 VALUES (%s, %s, %s, %s, %s, %s)
#             ''', (username, email, generate_password_hash(password), level, current_timestamp, current_timestamp))
#             mysql.connection.commit()
#             cursor.close()
#             return jsonify(success=True, message='Registration Success')
#         else:
#             cursor.close()
#             return jsonify(success=False, message='Username or Email already exists')
#     return render_template('users/user_list.html')

# @app.route('/user_edit')
# @login_required
# def user_edit():
#     return render_template('users/user_edit.html')

# delete user
# @app.route('/delete_user/<int:id>', methods=['POST'])
# # @login_required
# def delete_user(id):
#     try:
#         cursor = mysql.connection.cursor()
#         print(f'Deleting user with ID: {id}')
#         cursor.execute('DELETE FROM user_accounts WHERE id=%s', (id,))
#         mysql.connection.commit()  # Commit the changes
#         cursor.close()
#         flash('User deleted successfully', 'success')
#     except Exception as e:
#         print(f'Error deleting user: {e}')
#         flash('An error occurred while deleting the user', 'danger')
#     return redirect(url_for('user_list'))

# edit user
# @app.route('/user_edit/<int:id>', methods=['GET', 'POST'])
# def user_edit(id):
#     cursor = mysql.connection.cursor()

#     if request.method == 'POST':
#         username = request.form['username']
#         email = request.form['email']
#         level = request.form['level']
        
#         cursor.execute('UPDATE user_accounts SET username=%s, email=%s, level=%s, updated_at=%s WHERE id=%s',
#                        (username, email, level, datetime.now(), id))
#         mysql.connection.commit()
#         flash('User updated successfully', 'success')
#         return redirect(url_for('list_users'))
    
#     cursor.execute('SELECT id, username, email, level FROM user_accounts WHERE id=%s', (id,))
#     user = cursor.fetchone()
    
#     cursor.close()
#     return render_template('user_edit.html', user=user)



# @app.route('/user_edit')
# # @login_required
# def user_edit():
#     return render_template('users/user_edit.html')
# =================================================================================================================


# APP BACKUP 2024-08-19
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from functools import wraps
from flask_mysqldb import MySQL
from flask import Flask, Blueprint
from modules.auth import auth_blueprint
from modules.user import user_blueprint
from modules.entity import entity_blueprint
from modules.pr import pr_blueprint
import pandas as pd
from itsdangerous import URLSafeSerializer
import os

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
    app.config['MYSQL_HOST'] = '10.1.1.9'
    app.config['MYSQL_USER'] = 'rohman'
    app.config['MYSQL_PASSWORD'] = '!@#Bismillah'
    app.config['MYSQL_DB'] = 'playground'

    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_PATH'] = 16 * 1024 * 1024  # 16 MB max file size
    app.secret_key = 'prd'
    # SECRET_KEY=os.getenv('SECRET_KEY', 'your_secret_key')
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
# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'loggedin' not in session:
#             return redirect(url_for('auth.auth', next=request.url))
#         return f(*args, **kwargs)
#     return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            next_url = request.url
            # logging.debug(f"Redirecting to login, next URL: {next_url}")
            return redirect(url_for('auth.login', next=next_url))
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
# @app.context_processor
# def inject_menu_data():
#     if 'id' in session:
#         menu_data = get_menu_data(session['id'])
#     else:
#         menu_data = {}
#     return dict(menu_data=menu_data)

# @app.context_processor
# def utility_processor():
#     return dict(enumerate=enumerate)

# ================================================================================================================
# ENCRYPTION SETUP
# ================================================================================================================
# serializer = URLSafeSerializer(app.config['SECRET_KEY'])

# def encrypt_no_pr(no_pr):
#     return serializer.dumps(no_pr)

# def decrypt_no_pr(token):
#     try:
#         return serializer.loads(token)
#     except:
#         return None

# @app.context_processor
# def utility_processor():
#     context = {}
#     context['encrypt_no_pr'] = encrypt_no_pr
#     context['menu_data'] = get_menu_data(session.get('id', 0))
#     context['enumerate'] = enumerate
#     context['serializer'] = serializer  # Menambahkan serializer ke konteks template
#     return context

# @app.context_processor
# def utility_processor():
#     # Menggabungkan semua yang akan diinject ke dalam template context
#     context = {}

#     # Fungsi untuk enkripsi nomor PR
#     context['encrypt_no_pr'] = encrypt_no_pr

#     # Inject menu data jika session id ada
#     if 'id' in session:
#         context['menu_data'] = get_menu_data(session['id'])
#     else:
#         context['menu_data'] = {}

#     # Fungsi enumerate
#     context['enumerate'] = enumerate

#     return context

# ================================================================================================================
# ENCRYPTION SETUP
# ================================================================================================================
serializer = URLSafeSerializer(app.config['SECRET_KEY'])

def encrypt_id(id):
    return serializer.dumps(id)

def decrypt_id(token):
    try:
        return serializer.loads(token)
    except Exception as e:
        print(f"Decryption failed: {e}") 
        return None

@app.context_processor
def utility_processor():
    context = {}
    context['encrypt_id'] = encrypt_id
    context['menu_data'] = get_menu_data(session.get('id', 0))
    context['enumerate'] = enumerate
    context['serializer'] = serializer
    return context
# serializer = URLSafeSerializer(app.config['SECRET_KEY'])

# def encrypt_id(id):
#     return serializer.dumps(id)

# def decrypt_id(token):
#     try:
#         return serializer.loads(token)
#     except Exception as e:
#         print(f"Decryption failed: {e}")  # Debugging message
#         return None


# @app.context_processor
# def utility_processor():
#     return dict(
#         encrypt_id=encrypt_id,
#         decrypt_id=decrypt_id,
#         menu_data =  get_menu_data(session.get('id', 0)),
#         enumerate=enumerate
#     )

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
    app.run(host='10.1.1.9', port=5000, debug=True)
    
    # MY MAC__________________________________________
    # app.run(host='10.0.13.247', port=5000, debug=True)

    # ON PREM_________________________________________
    # app.run(host='10.0.13.53', port=5000, debug=True)
   
    # ON PREM DEV_____________________________________
    # app.run(host='10.0.12.53', port=1213, debug=True)

# ================================================================================================================


# APP BACKUP 2024-09-11
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
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

# ================================================================================================================
# MYSQL CONNNECTION SETUP PARAMETER 
# ================================================================================================================
def appFlask():
    app = Flask(__name__)

    # DB CONN MY MAC_________________________________________
    app.config['MYSQL_HOST'] = '10.0.13.247' 
    app.config['MYSQL_USER'] = 'rohman'
    app.config['MYSQL_PASSWORD'] = '!@#Bismillah'
    app.config['MYSQL_DB'] = 'playground'

    # DB ONPREM_______________________________________________
    # app.config['MYSQL_HOST'] = '10.0.12.53' 
    # app.config['MYSQL_USER'] = 'data-tech'
    # app.config['MYSQL_PASSWORD'] = '!@#Bismill4h'
    # app.config['MYSQL_DB'] = 'erp'

    # DB HOME_________________________________________________
    # app.config['MYSQL_HOST'] = '10.1.1.9'
    # app.config['MYSQL_USER'] = 'rohman'
    # app.config['MYSQL_PASSWORD'] = '!@#Bismillah'
    # app.config['MYSQL_DB'] = 'playground'

    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['ENTITY_UPLOAD_FOLDER'] = 'static/entity_logo'
    app.config['MAX_CONTENT_PATH'] = 16 * 1024 * 1024  # 16 MB max file size
    app.secret_key = 'prd'
    # SECRET_KEY=os.getenv('SECRET_KEY', 'your_secret_key')
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
# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'loggedin' not in session:
#             return redirect(url_for('auth.auth', next=request.url))
#         return f(*args, **kwargs)
#     return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            next_url = request.url
            # logging.debug(f"Redirecting to login, next URL: {next_url}")
            return redirect(url_for('auth.login', next=next_url))
        return f(*args, **kwargs)
    return decorated_function


# FILTER USER BY MENU
def get_menu_data(user_id):

    # tambahkan route untuk module menu baru berdasarkan id_menu di db
    menu_url = {
        1: 'user.user_list',
        3: 'entity.entity_list',
        4: 'pr.pr_list',
        5: 'prf.prf_list',
        6: 'woc.woc_list',
        7: 'vendor.vendor_list'
    }

    # tambahkan icon untuk module menu baru berdasarkan id_menu di db
    menu_icon = {
        1: 'nav-icon far fa-user',
        3: 'nav-icon far fa-building',
        4: 'nav-icon far fa-edit',
        5: 'nav-icon far fa-edit',
        6: 'nav-icon far fa-edit',
        7: 'nav-icon far fa-handshake'
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
# def inject_menu_data():
#     if 'id' in session:
#         menu_data = get_menu_data(session['id'])
#     else:
#         menu_data = {}
#     return dict(menu_data=menu_data)

# @app.context_processor
# def utility_processor():
#     return dict(enumerate=enumerate)


# ================================================================================================================
# ENCRYPTION SETUP
# ================================================================================================================
serializer = URLSafeSerializer(app.config['SECRET_KEY'])

def encrypt_id(id):
    return serializer.dumps(id)

def decrypt_id(token):
    try:
        return serializer.loads(token)
    except Exception as e:
        print(f"Decryption failed: {e}") 
        return None

@app.context_processor
def utility_processor():
    context = {}
    context['encrypt_id'] = encrypt_id
    context['menu_data'] = get_menu_data(session.get('id', 0))
    context['enumerate'] = enumerate
    context['serializer'] = serializer
    return context


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
app.register_blueprint(prf_blueprint)
app.register_blueprint(vendor_blueprint)
app.register_blueprint(woc_blueprint)

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
    # app.run(host='10.1.1.9', port=5000, debug=True)
    
    # MY MAC__________________________________________
    app.run(host='10.0.13.247', port=5000, debug=True)

    # ON PREM_________________________________________
    # app.run(host='10.0.13.53', port=5000, debug=True)
   
    # ON PREM DEV_____________________________________
    # app.run(host='10.0.12.53', port=1213, debug=True)

# ================================================================================================================