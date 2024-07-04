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
pr_blueprint = Blueprint('pr', __name__)


# LIST USER
@pr_blueprint.route('/pr_add')
@login_required
# @check_access(menu_id=1)
def pr_add():
    from app import mysql
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM purchase_requisition')
    list = cursor.fetchall()

    cursor.close()
    return render_template('pr/pr_add.html', list=list)
