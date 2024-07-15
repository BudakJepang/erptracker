from flask import Blueprint, redirect, render_template, request, session, url_for, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from modules.time import convert_time_to_wib
from datetime import datetime, timedelta, timezone
from modules.decorator import login_required, check_access
from functools import wraps


# LOCK REQUIRED TO LOGIN
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('auth.auth'))
        return f(*args, **kwargs)
    return decorated_function


# BLUEPRINT AUTH VARIABLE
user_blueprint = Blueprint('user', __name__)


# LIST USER
@user_blueprint.route('/user_list')
@login_required
# @check_access(menu_id=1)
def user_list():
    from app import mysql
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, username, email, level, created_at, created_by, updated_at, updated_by FROM user_accounts')
    users = cursor.fetchall()

    cursor.close()
    return render_template('users/user_list.html', users=users)


# REGISTRATION AND ACCESS USER
@user_blueprint.route('/register', methods=('GET', 'POST'))
@login_required
def register():
    from app import mysql
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        level = request.form['level']
        selected_menus = request.form.getlist('menus')  # ambil daftar menu yang dipilih dari view html
        selected_entities = request.form.getlist('entities')  # ambil daftar entity yang dipilih dari view html

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT username, email FROM user_accounts WHERE username=%s OR email=%s', (username, email))
        account = cursor.fetchone()
        
        if account is None:
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            created_by = session.get('username', 'system')  # get the username of the logged in user or 'system'
            cursor.execute('''
                INSERT INTO user_accounts (username, email, password, level, created_at, updated_at, created_by, updated_by) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (username, email, generate_password_hash(password), level, current_timestamp, current_timestamp, created_by, created_by))
            mysql.connection.commit()
            user_id = cursor.lastrowid  # get ID user yang baru saja dibuat

            # simpan data menu yang dipilih ke tabel access_users
            for menu_id in selected_menus:
                cursor.execute('''
                    INSERT INTO access_users (id_user, id_menu, created_at, updated_at, created_by, updated_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (user_id, menu_id, current_timestamp, current_timestamp, created_by, created_by))
            
            # simpan data entity yang dipilih ke tabel user_entity
            for entity_id in selected_entities:
                cursor.execute('''
                    INSERT INTO user_entity (user_id, entity_id, created_at, updated_at)
                    VALUES (%s, %s, %s, %s)
                ''', (user_id, entity_id, current_timestamp, current_timestamp))

            # simpan data department yang dipilih ke tabel user_department
            for entity_id in selected_entities:
                cursor.execute('''
                    INSERT INTO user_department (user_id, department_id, created_at, updated_at)
                    VALUES (%s, %s, %s, %s)
                ''', (user_id, entity_id, current_timestamp, current_timestamp))
            
            mysql.connection.commit()
            cursor.close()
            flash('Registration Success', 'success')
            return redirect(url_for('user.user_list'))
        else:
            cursor.close()
            flash('Username or Email already exists', 'danger')
            return redirect(url_for('user.register'))
    
    # Ambil data menu dan entity dari database untuk ditampilkan di form
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, menu_name FROM menu')
    all_menus = cursor.fetchall()
    cursor.execute('SELECT id, entity_name FROM entity')
    all_entities = cursor.fetchall()
    cursor.execute('SELECT id, department, department_name FROM department WHERE entity_id = 1')
    all_department = cursor.fetchall()
    cursor.close()
    
    return render_template('users/user_add.html', all_menus=all_menus, all_entities=all_entities, all_department=all_department)



# CHANGE USER PASSWORD AS A USER
@user_blueprint.route('/user_change_password/<int:id>', methods=['GET', 'POST'])
@login_required
def user_change_password(id):
    from app import mysql
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        user_id = request.form['id_user']
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
            return redirect(url_for('user.user_list'))
        else:
            # Current password is incorrect
            flash('Current password is incorrect', 'danger')
            
        return redirect(url_for('user.user_change_password', id=user_id))
    
    cursor.execute('SELECT id, username, email, level FROM user_accounts WHERE id=%s', (id,))
    user = cursor.fetchone()
    cursor.close()

    if user is None:
        flash('User not found', 'danger')
        return redirect(url_for('user.list_users'))
    
    return render_template('users/user_change_password.html', user=user)


# USER SETTINGS
@user_blueprint.route('/user_settings')
@login_required
def user_settings():
    from app import mysql
    user_id = session.get('user_id')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, username FROM users_account WHERE id=%s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    
    return render_template('base.html', user=user)


# EDIT USER AS USER ADMIN
@user_blueprint.route('/user_edit/<int:user_id>', methods=('GET', 'POST'))
@login_required
def user_edit(user_id):
    from app import mysql
    
    cursor = mysql.connection.cursor()
    
    # get data user
    cursor.execute('''SELECT 
                    id AS id_user, 
                    username, 
                    email, 
                    level
                    FROM user_accounts
                    WHERE id = %s''', (user_id,))
    user = cursor.fetchone() # get user untuk ditampilkan datanya pada form HTML
    
    if user is None:
        flash('User not found', 'danger')
        return redirect(url_for('user.user_list'))
    
    # get all menus untuk list menu pada html
    cursor.execute('SELECT id, menu_name FROM menu')
    all_menus = cursor.fetchall() # value ini akan kita kirim pada list menu checkbox HTML untuk dilooping
    
    # get access menu untuk user apa saja listnya
    cursor.execute('SELECT id_menu FROM access_users WHERE id_user = %s', (user_id,))
    current_menus = cursor.fetchall()
    current_menus = {menu[0] for menu in current_menus}
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        level = request.form['level']
        updated_by = session.get('username', 'system')
        selected_menus = request.form.getlist('menus') 
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            UPDATE user_accounts 
            SET username = %s, email = %s, level = %s, updated_at = %s, updated_by = %s
            WHERE id = %s
        ''', (username, email, level, current_timestamp, updated_by, user_id))
        
        # menentukan yang mau dihapus atau ditambahkan
        selected_menus = set(int(menu_id) for menu_id in selected_menus)
        menus_to_add = selected_menus - current_menus
        menus_to_remove = current_menus - selected_menus

        # delete menu yang dimiliki user jika mau ditakedown accessnya
        if menus_to_remove:
            cursor.executemany('DELETE FROM access_users WHERE id_user = %s AND id_menu = %s', 
                               [(user_id, menu_id) for menu_id in menus_to_remove])
        
        # menambahkan menu pada user
        for menu_id in menus_to_add:
            cursor.execute('''
                INSERT INTO access_users (id_user, id_menu, created_at, updated_at, created_by, updated_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, menu_id, current_timestamp, current_timestamp, updated_by, updated_by))
        
        mysql.connection.commit()
        cursor.close()
        
        flash('User updated successfully', 'success')
        return redirect(url_for('user.user_list'))
    
    user_data = {
        'id': user[0],
        'username': user[1],
        'email': user[2],
        'level': user[3]
    }
    
    return render_template('users/user_edit.html', user=user_data, all_menus=all_menus, current_menus=current_menus)


# DELETE USER
@user_blueprint.route('/delete_user/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    from app import mysql
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM user_accounts WHERE id = %s', (id,))
    mysql.connection.commit()
    cursor.close()
    flash('User has been deleted successfully', 'success')
    return redirect(url_for('user.user_list'))


# GET LIST MENU ON LIST USERS AS JSON RETURN (peruntukan ketika register untuk modal json)
@user_blueprint.route('/get_menus', methods=['GET'])
def get_menus():
    from app import mysql
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, menu_name FROM menu')
    menus = cursor.fetchall()
    cursor.close()
    return jsonify(menus) 