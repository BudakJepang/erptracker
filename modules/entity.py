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
    cursor.execute('SELECT username FROM user_accounts')
    entity = cursor.fetchall()

    cursor.close()
    return render_template('entity/entity_list.html', entity=entity)
