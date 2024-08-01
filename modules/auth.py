from flask import Blueprint, redirect, render_template, request, session, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash


# BLUEPRINT AUTH VARIABLE
auth_blueprint = Blueprint('auth', __name__)

# AUTH VIEW
@auth_blueprint.route('/auth')
def auth():
    return render_template('auth/login.html')

# LOGIN
@auth_blueprint.route('/login', methods=('GET','POST'))
def login():
    from app import mysql
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # check users data
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id, username, email, password, level FROM user_accounts WHERE email=%s', (email,))
        account = cursor.fetchone()
        
        # account validation 
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
            session['email'] = account[2]

            # get filter user as entity
            cursor.execute('''
                SELECT ue.entity_id, e.entity_name
                FROM user_entity ue
                LEFT JOIN entity e ON ue.entity_id = e.id
                WHERE ue.user_id = %s
            ''', (account[0],))
            entities = cursor.fetchall()
            session['entities'] = [{'entity_id': entity[0], 'entity_name': entity[1]} for entity in entities]
            cursor.close()
            return redirect(url_for('index'))
        
    return render_template('auth/login.html')

# LOGOUT
@auth_blueprint.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    session.pop('level', None)
    session.pop('email', None)
    return redirect(url_for('auth.login'))