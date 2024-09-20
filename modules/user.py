import os
from flask import Blueprint, redirect, render_template, request, session, url_for, flash, jsonify, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from modules.time import convert_time_to_wib
from datetime import datetime, timedelta, timezone
from modules.helper import login_required, menu_access_required



# BLUEPRINT AUTH VARIABLE
user_blueprint = Blueprint('user', __name__)
# ====================================================================================================================================


# ====================================================================================================================================
# GET LIST MENU ON LIST USERS AS JSON RETURN (peruntukan ketika register untuk modal json)
# ====================================================================================================================================
@user_blueprint.route('/get_menus', methods=['GET'])
def get_menus():
    from app import mysql
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, menu_name FROM menu')
    menus = cursor.fetchall()
    cursor.close()
    return jsonify(menus) 
# ====================================================================================================================================



# ====================================================================================================================================
# LIST USER
# ====================================================================================================================================
@user_blueprint.route('/user_list')
@login_required
@menu_access_required(1)
def user_list():
    from app import mysql
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, username, email, level, created_at, created_by, updated_at, updated_by FROM user_accounts')
    users = cursor.fetchall()

    cursor.close()
    return render_template('users/user_list.html', users=users)
# ====================================================================================================================================


# ====================================================================================================================================
# REGISTRATION AND ACCESS USER
# ====================================================================================================================================
@user_blueprint.route('/register', methods=('GET', 'POST'))
@user_blueprint.route('/register/<encrypted_user_id>', methods=('GET', 'POST'))
# @user_blueprint.route('/register/<int:user_id>', methods=('GET', 'POST'))
@login_required
@menu_access_required(1)
def register(encrypted_user_id=None):
# def register(user_id=None):
    from app import mysql
    from app import decrypt_id
    cursor = mysql.connection.cursor()

    # protect hit link using the id_user
    user_id = None
    if encrypted_user_id:
        user_id = decrypt_id(encrypted_user_id)
        if not user_id:
            flash('Invalid User ID', 'danger')
            return redirect(url_for('user.user_list'))
            # return "Invalid ID", 400

    user = None
    user_menus = []
    user_entities = []

    cursor.execute('SELECT id, menu_name FROM menu')
    all_menus = cursor.fetchall()
    cursor.execute('SELECT id, entity_name FROM entity')
    all_entities = cursor.fetchall()
    cursor.execute('SELECT id, department, department_name FROM department WHERE entity_id = 1')
    all_department = cursor.fetchall()

    if user_id:
        cursor.execute('SELECT * FROM user_accounts WHERE id=%s', (user_id,))
        user = cursor.fetchone()

        cursor.execute('SELECT id_menu FROM user_access WHERE id_user=%s', (user_id,))
        user_menus = [row[0] for row in cursor.fetchall()]

        cursor.execute('SELECT entity_id FROM user_entity WHERE user_id=%s', (user_id,))
        user_entities = [row[0] for row in cursor.fetchall()]

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        level = request.form['level']
        selected_menus = request.form.getlist('menus')
        selected_entities = request.form.getlist('entities')
        
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        created_by = session.get('username', 'system')

        if user_id:
            cursor.execute('''
                UPDATE user_accounts
                SET username=%s, email=%s, password=%s, level=%s, updated_at=%s, updated_by=%s
                WHERE id=%s
            ''', (username, email, generate_password_hash(password), level, current_timestamp, created_by, user_id))

            cursor.execute('DELETE FROM user_access WHERE id_user=%s', (user_id,))
            cursor.execute('DELETE FROM user_entity WHERE user_id=%s', (user_id,))
        else:
            cursor.execute('SELECT username, email FROM user_accounts WHERE username=%s OR email=%s', (username, email))
            account = cursor.fetchone()

            if account is None:
                cursor.execute('''
                    INSERT INTO user_accounts (username, email, password, level, created_at, updated_at, created_by, updated_by) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (username, email, generate_password_hash(password), level, current_timestamp, current_timestamp, created_by, created_by))
                user_id = cursor.lastrowid
            else:
                flash('Username or Email already exists', 'danger')
                return redirect(url_for('user.register'))

        for menu_id in selected_menus:
            cursor.execute('''
                INSERT INTO user_access (id_user, id_menu, created_at, updated_at, created_by, updated_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, menu_id, current_timestamp, current_timestamp, created_by, created_by))

        for entity_id in selected_entities:
            cursor.execute('''
                INSERT INTO user_entity (user_id, entity_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, entity_id, current_timestamp, current_timestamp))

        mysql.connection.commit()
        flash('User saved successfully', 'success')
        return redirect(url_for('user.user_list'))

    cursor.close()
    return render_template('users/user_add.html', user=user, user_menus=user_menus, user_entities=user_entities, all_menus=all_menus, all_entities=all_entities, all_department=all_department)
# ====================================================================================================================================


# ====================================================================================================================================
# CHANGE USER PASSWORD AS A USER
# ====================================================================================================================================
# @user_blueprint.route('/user_change_password/<int:id>', methods=['GET', 'POST'])
@user_blueprint.route('/user_change_password/<encrypted_user_id>',  methods=['GET', 'POST'])
@login_required
# @menu_access_required(1)
def user_change_password(encrypted_user_id=None):
    from app import mysql
    from app import decrypt_id
    cursor = mysql.connection.cursor()

    id = None
    if encrypted_user_id:
        id = decrypt_id(encrypted_user_id)
        if not id:
            flash('Invalid User ID', 'danger')
            # return redirect(url_for('user.user_list'))
            return f"{encrypted_user_id}"

    cursor.execute('SELECT password, sign_path FROM user_accounts WHERE id=%s', (id,))
    user = cursor.fetchone()

    if request.method == 'POST':
        user_id = request.form['user_id']
        username = request.form['username']
        email = request.form['email']
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        signature = request.files.get('signature')

        # Check if the current password is correct
        if user and check_password_hash(user[0], current_password):
            updates = {
                "username": username,
                "email": email,
                "updated_at": datetime.now()
            }

            # If a new password is provided, hash it and include it in the update
            if new_password:
                updates["password"] = generate_password_hash(new_password)

            # If a new signature is uploaded, save it and include the path in the update
            if signature and signature.filename != '':
                signature_filename = secure_filename(signature.filename)
                signature_path = os.path.join('static/uploads', signature_filename)
                signature.save(os.path.join(current_app.config['UPLOAD_FOLDER'], signature_filename))
                updates["sign_path"] = signature_path

            # Generate the SQL query dynamically based on what needs to be updated
            set_clause = ", ".join(f"{key}=%s" for key in updates.keys())
            values = list(updates.values())
            values.append(user_id)

            cursor.execute(f'''
                UPDATE user_accounts 
                SET {set_clause}
                WHERE id=%s
            ''', values)

            mysql.connection.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Current password is incorrect', 'warning')

        return redirect(url_for('user.user_change_password', id=user_id))

    cursor.execute('SELECT id, username, email, level, sign_path FROM user_accounts WHERE id=%s', (id,))
    user = cursor.fetchone()
    user = list(user)
    if user[4] is not None:
        user[4] = user[4].replace("static/", "")
    else:
        pass
    cursor.close()

    if user is None:
        flash('User not found', 'warning')
        return redirect(url_for('index'))

    return render_template('users/user_change_password.html', user=user)

# ====================================================================================================================================


# ====================================================================================================================================
# USER SETTINGS
# ====================================================================================================================================
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
# ====================================================================================================================================


# ====================================================================================================================================
# EDIT USER AS USER ADMIN
# ====================================================================================================================================
@user_blueprint.route('/user_edit/<int:user_id>', methods=('GET', 'POST'))
@login_required
@menu_access_required(1)
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
    cursor.execute('SELECT id_menu FROM user_access WHERE id_user = %s', (user_id,))
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
            cursor.executemany('DELETE FROM user_access WHERE id_user = %s AND id_menu = %s', 
                               [(user_id, menu_id) for menu_id in menus_to_remove])
        
        # menambahkan menu pada user
        for menu_id in menus_to_add:
            cursor.execute('''
                INSERT INTO user_access (id_user, id_menu, created_at, updated_at, created_by, updated_by)
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
# ====================================================================================================================================


# ====================================================================================================================================
# DELETE USER
# ====================================================================================================================================
@user_blueprint.route('/delete_user/<int:id>', methods=['POST'])
@login_required
@menu_access_required(1)
def delete_user(id):
    from app import mysql
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM user_accounts WHERE id = %s', (id,))
    mysql.connection.commit()
    cursor.close()
    flash('User has been deleted successfully', 'success')
    return redirect(url_for('user.user_list'))
# ====================================================================================================================================