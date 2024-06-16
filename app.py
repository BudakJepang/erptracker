from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import pytz

def convert_time_to_wib(dtobject):
    tz = pytz.timezone('Asia/Jakarta')
    utc = pytz.timezone('UTC')
    tz_aware = utc.localize(dtobject)
    localtime = tz_aware.astimezone(tz)
    return localtime

# current_timestamp = convert_time_to_wib(datetime.now()).strftime("%Y-%m-%d %H%M%S")
current_timestamp = datetime.now()

app = Flask(__name__)

# DB CONNECTION
app.secret_key = 'testing'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'popey'
app.config['MYSQL_PASSWORD'] = 'Kpaii1234'
app.config['MYSQL_DB'] = 'playground'
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/home')
def home():
    return render_template('home.html')

# AUTHENTICATION ROUTE ===========================================================================================
# login
@app.route('/login', methods=('GET','POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # check users data
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT username, email, password, level FROM user_accounts WHERE email=%s', (email,))
        account = cursor.fetchone()
        
        if account is None:
            flash('Login failed, please check your username', 'danger')
        elif not check_password_hash(account[2], password):
            flash('Login failed, check your password is correct', 'danger')
        else:
            session['loggedin'] = True
            session['username'] = account[1]
            session['level'] = account[3]
            return redirect(url_for('index'))
        
    return render_template('auth/login.html')

# logout
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    session.pop('level', None)
    return redirect(url_for('login'))
# ===============================================================================================================

# USER ROUTE ====================================================================================================
# list user
@app.route('/user_list')
# @login_required
def list_users():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, username, email, level, created_at FROM user_accounts')
    users = cursor.fetchall()

    cursor.close()
    return render_template('users/user_list.html', users=users)


# registration
@app.route('/register', methods=('GET','POST'))
# @login_required
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        level = request.form['level']
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM user_accounts WHERE username=%s OR email=%s', (username, email))
        account = cursor.fetchone()
        
        if account is None:
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO user_accounts (username, email, password, level, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (username, email, generate_password_hash(password), level, current_timestamp, current_timestamp))
            mysql.connection.commit()
            cursor.close()
            flash('Registration Success', 'success')
            return redirect(url_for('register'))
        else:
            cursor.close()
            flash('Username or Email already exists', 'danger')
            return redirect(url_for('register'))
    return render_template('users/user_add.html')


# @app.route('/user_edit')
# # @login_required
# def user_edit():
#     return render_template('users/user_edit.html')


# edit user
# @app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
# def edit_user(id):
#     cursor = mysql.connection.cursor()

#     if request.method == 'POST':
#         username = request.form['username']
#         email = request.form['email']
#         level = request.form['level']
        
#         cursor.execute('UPDATE users_account SET username=%s, email=%s, level=%s, updated_at=%s WHERE id=%s',
#                        (username, email, level, datetime.now(), id))
#         mysql.connection.commit()
#         flash('User updated successfully', 'success')
#         return redirect(url_for('list_users'))
    
#     cursor.execute('SELECT id, username, email, level FROM users_account WHERE id=%s', (id,))
#     user = cursor.fetchone()
    
#     cursor.close()
#     return render_template('edit_user.html', user=user)


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
#     return redirect(url_for('list_users'))

# ==================================================================================================================

if __name__ == '__main__':
    app.run(debug=True)
