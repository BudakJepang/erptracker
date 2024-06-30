from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from functools import wraps
from flask_mysqldb import MySQL
from flask import Flask, Blueprint
from modules.auth import auth_blueprint
from modules.user import user_blueprint
import pandas as pd


# ================================================================================================================
# MYSQL CONNNECTION SETUP PARAMETER 
# ================================================================================================================
def appFlask():
    app = Flask(__name__)
    app.config['MYSQL_HOST'] = '10.1.1.9'
    app.config['MYSQL_USER'] = 'rohman'
    app.config['MYSQL_PASSWORD'] = '!@#Bismillah'
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


# LOCK REQUIRED TO LOGIN
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('auth.auth'))
        return f(*args, **kwargs)
    return decorated_function

# def get_menu_data(user_id):
    
#     # Define the initial data as a DataFrame
#     dataTable = {
#         'id_menu': [1],
#         'id_category': [3],
#         'link_menu': ['user.user_list'],
#         'icon_menu': ['nav-icon far fa-user']
#     }
#     menu_link = pd.DataFrame(dataTable)

#     # Fetch data from the database
#     cursor = mysql.connection.cursor()
#     cursor.execute('''
#         SELECT 
#         cat.id AS id_category, m.id AS id_menu, cat.category_name,
#         m.menu_name 
#         FROM playground.category_menu as cat
#         LEFT JOIN playground.menu AS m on cat.id = m.id_category
#         LEFT JOIN playground.access_users AS au on m.id = au.id_menu 
#         WHERE au.id_user = %s
#     ''', (user_id,))
#     data = cursor.fetchall()
#     cursor.close()

#     # Convert fetched data to DataFrame
#     data_df = pd.DataFrame(data, columns=['id_category', 'id_menu', 'category_name', 'menu_name'])

#     # Perform the join operation
#     merged_df = pd.merge(menu_link, data_df, on='id_menu', how='inner')

#     # Process the merged DataFrame to structure the menu data
#     menu_data = {}
#     for _, row in merged_df.iterrows():
#         category_name = row['category_name']
#         menu_item = {
#             'name': row['menu_name'],
#             'link': row['link_menu'],
#             'icon': row['icon_menu']
#         }

#         if category_name not in menu_data:
#             menu_data[category_name] = []

#         menu_data[category_name].append(menu_item)

#     return menu_data

# FILTER USER BY MENU
def get_menu_data(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute('''
        SELECT 
        cat.id, cat.category_name,
        m.menu_name 
        FROM category_menu as cat
        LEFT JOIN menu AS m on cat.id = m.id_category
        LEFT JOIN access_users AS au on m.id = au.id_menu 
        WHERE au.id_user = %s
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
# BAKCUP


# AUTHORIZE MENU ACCESS
@app.context_processor
def inject_menu_data():
    if 'id' in session:
        menu_data = get_menu_data(session['id'])
    else:
        menu_data = {}
    return dict(menu_data=menu_data)

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

# ================================================================================================================
# ALL FUNCTION ROUTE
# ================================================================================================================
app.register_blueprint(auth_blueprint)
app.register_blueprint(user_blueprint)
# ================================================================================================================ 
# ================================================================================================================

@app.route('/')
@login_required
def index():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(host='10.1.1.9', port=5000, debug=True)