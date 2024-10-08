import os
from flask import Blueprint, redirect, render_template, request, session, url_for, flash, jsonify, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
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
    cursor.execute('SELECT id, entity, entity_name, logo_path FROM entity')
    entity = cursor.fetchall()

    cursor.close()
    return render_template('entity/entity_list.html', entity=entity)

# ====================================================================================================================================
# ENTITY ADD AND EDIT
# ====================================================================================================================================
@entity_blueprint.route('/entity_add', methods=('GET', 'POST'))
@entity_blueprint.route('/entity_add/<int:entity_id>', methods=('GET', 'POST'))
@login_required
def entity_add(entity_id=None):
    from app import mysql
    cursor = mysql.connection.cursor()
    logo = request.files.get('logo')
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    created_by = session.get('username', 'system')

    # If a new logo is uploaded, save it and include the path in the update
    if logo and logo.filename != '':
        logo_filename = secure_filename(logo.filename)
        logo_path = os.path.join(current_app.config['ENTITY_UPLOAD_FOLDER'], logo_filename)
        logo.save(logo_path)
        logo_path = logo_path
    else:
        logo_filename=""

    if entity_id:
        cursor.execute('SELECT * FROM entity WHERE id=%s', (entity_id,))
        entity = cursor.fetchone()
        if request.method == 'POST':
            entity_code = request.form['entity_code']
            entity_name = request.form['entity_name']
            
            cursor.execute('''
                    UPDATE entity
                    SET entity=%s, entity_name=%s, updated_at=%s, logo_path=%s
                    WHERE id=%s
                ''', (entity_code, entity_name, current_timestamp, logo_path, entity_id))
            mysql.connection.commit()
            flash('Entity saved successfully', 'success')
            return redirect(url_for('entity.entity_list'))
    else:
        entity=[]
        if request.method == 'POST':
            entity_code = request.form['entity_code']
            entity_name = request.form['entity_name']

            cursor.execute('''
                INSERT INTO entity (entity, entity_name, logo_path, created_at, updated_at) 
                VALUES (%s, %s, %s, %s, %s)
                ''', (entity_code, entity_name, logo_path, current_timestamp, current_timestamp))
            mysql.connection.commit()
            flash('Entity saved successfully', 'success')
            return redirect(url_for('entity.entity_list'))
    cursor.close()
    return render_template('entity/entity_add.html', entity=entity)
# ====================================================================================================================================