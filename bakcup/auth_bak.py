# AUTH BAK 2024-09-12
from flask import Blueprint, redirect, render_template, request, session, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import logging
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# BLUEPRINT AUTH VARIABLE
auth_blueprint = Blueprint('auth', __name__)

# AUTH VIEW
@auth_blueprint.route('/auth')
def auth():
    return render_template('auth/login.html')


# LOGIN
@auth_blueprint.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        from app import mysql
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id, username, email, password, level FROM user_accounts WHERE email=%s', (email,))
        account = cursor.fetchone()
        
        if account is None:
            flash('Login failed, please check your username', 'warning')
        elif not check_password_hash(account[3], password):
            flash('Login failed, check your password is correct', 'warning')
        else:
            session.clear()
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            session['level'] = account[4]
            session['email'] = account[2]

            cursor.execute('''
                SELECT ue.entity_id, e.entity_name
                FROM user_entity ue
                LEFT JOIN entity e ON ue.entity_id = e.id
                WHERE ue.user_id = %s
            ''', (account[0],))
            entities = cursor.fetchall()
            session['entities'] = [{'entity_id': entity[0], 'entity_name': entity[1]} for entity in entities]
            cursor.close()
            
            # Get the next URL if present
            next_url = request.args.get('next')
            # logging.basicConfig(level=logging.DEBUG)
            # logging.debug(f"Next URL URL URL URL URL URL URL URL URL: {next_url}")
            return redirect(next_url or url_for('index'))
            # return f'{next_url}'
    return render_template('auth/login.html')


# LOGOUT
@auth_blueprint.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    session.pop('level', None)
    session.pop('email', None)
    return redirect(url_for('auth.login'))


# JWT AUTH LOGIN
# LOGIN
@auth_blueprint.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        from app import mysql
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id, username, email, password, level FROM user_accounts WHERE email=%s', (email,))
        account = cursor.fetchone()

        if account is None:
            flash('Login failed, please check your username', 'warning')
        elif not check_password_hash(account[3], password):
            flash('Login failed, check your password is correct', 'warning')
        else:
            session.clear()
            # Buat token JWT jika login berhasil
            access_token = create_access_token(identity={
                'id': account[0],
                'username': account[1],
                'email': account[2],
                'level': account[4]
            })
            session['access_token'] = access_token
            
            # Mendapatkan entitas user
            cursor.execute('''
                SELECT ue.entity_id, e.entity_name
                FROM user_entity ue
                LEFT JOIN entity e ON ue.entity_id = e.id
                WHERE ue.user_id = %s
            ''', (account[0],))
            entities = cursor.fetchall()
            session['entities'] = [{'entity_id': entity[0], 'entity_name': entity[1]} for entity in entities]
            cursor.close()
            
            # Dapatkan URL tujuan setelah login
            next_url = request.args.get('next')
            return redirect(next_url or url_for('index'))
            
    return render_template('auth/login.html')