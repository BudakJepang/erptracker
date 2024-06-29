from functools import wraps
from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import pytz
import random
import hashlib
from functools import wraps


user_blueprint = Blueprint('user', __name__)
# ================================================================================================================
# USERS & REGISTER ROUTE 
# ================================================================================================================
# list user
@app.route('/user_list')
@user_blueprint.route('/user')
@login_required
def user_list():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, username, email, level, created_at FROM user_accounts')
    users = cursor.fetchall()

    cursor.close()
    return render_template('users/user_list.html', users=users)


# registration and access user
@user_blueprint.route('/user_list')
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
# END USERS ROUTE 
# ================================================================================================================