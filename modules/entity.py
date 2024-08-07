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
entity_blueprint = Blueprint('entity', __name__)


# LIST USER
@entity_blueprint.route('/entity_list')
@login_required
# @check_access(menu_id=1)
def entity_list():
    from app import mysql
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, entity, entity_name FROM entity')
    entity = cursor.fetchall()

    cursor.close()
    return render_template('entity/entity_list.html', entity=entity)

# FORM
@entity_blueprint.route('/entity_form', methods=('GET', 'POST'))
@entity_blueprint.route('/entity_form/<int:user_id>', methods=('GET', 'POST'))
@login_required
def entity_form(user_id=None):
    from app import mysql
    cursor = mysql.connection.cursor()

    user = None
    #user_menus = []
    entities = []

    if user_id:
        #cursor.execute('SELECT * FROM entity WHERE id=%s', (user_id,))
        #user = cursor.fetchone()

       # cursor.execute('SELECT id_menu FROM user_access WHERE id_user=%s', (user_id,))
       # user_menus = [row[0] for row in cursor.fetchall()]

        cursor.execute('SELECT entity_id FROM entity WHERE user_id=%s', (user_id,))
        entities = [row[0] for row in cursor.fetchall()]

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
                mysql.connection.commit()
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
        cursor.close()
        flash('User saved successfully', 'success')
        return redirect(url_for('user.user_list'))

    cursor.execute('SELECT id, menu_name FROM menu')
    all_menus = cursor.fetchall()
    cursor.execute('SELECT id, entity_name FROM entity')
    all_entities = cursor.fetchall()
    cursor.execute('SELECT id, department, department_name FROM department WHERE entity_id = 1')
    all_department = cursor.fetchall()
    cursor.close()

    return render_template('entity/entity_add.html', user=user,  all_menus=all_menus, all_entities=all_entities, all_department=all_department)
