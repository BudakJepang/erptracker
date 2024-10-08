from flask import Blueprint, redirect, render_template, request, session, url_for, flash, abort
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import logging

# BLUEPRINT AUTH VARIABLE
auth_blueprint = Blueprint('auth', __name__)

# ==============================================================================================================
# AUTH VIEW
# ==============================================================================================================
@auth_blueprint.route('/auth')
def auth():
    return render_template('auth/login.html')
# ==============================================================================================================


# ==============================================================================================================
# LOGIN
# ==============================================================================================================
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

            cursor.execute("SELECT id_menu FROM user_access WHERE id_user=%s", (account[0],))
            menus = cursor.fetchall()
            session['menu'] = [menu[0] for menu in menus]

            cursor.close()
            
            # Get the next URL if present
            next_url = request.args.get('next')
            # logging.basicConfig(level=logging.DEBUG)
            # logging.debug(f"Next URL URL URL URL URL URL URL URL URL: {next_url}")
            return redirect(next_url or url_for('index'))
            # return f'{next_url}'
    return render_template('auth/login.html')
# ==============================================================================================================


# ==============================================================================================================
# LOGOUT
# ==============================================================================================================
@auth_blueprint.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    session.pop('level', None)
    session.pop('email', None)
    return redirect(url_for('auth.login'))
# ==============================================================================================================
