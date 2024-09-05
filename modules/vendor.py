from flask import Blueprint, redirect, render_template, request, session, url_for, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from modules.time import convert_time_to_wib
from datetime import datetime, timedelta, timezone
from modules.decorator import login_required, check_access
from functools import wraps
from flask_mysqldb import MySQL, MySQLdb


# LOCK REQUIRED TO LOGIN
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('auth.auth'))
        return f(*args, **kwargs)
    return decorated_function


# BLUEPRINT VENDOR VARIABLE
vendor_blueprint = Blueprint('vendor', __name__)

# LIST VENDOR
@login_required
@vendor_blueprint.route('/vendor_list')
def vendor_list():
    from app import mysql
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM vendor')
    vendor = cur.fetchall()
    cur.close()
    return render_template('vendor/vendor_list.html', vendor=vendor)

# ADD/SUBMIT & EDIT VENDOR
@vendor_blueprint.route('/vendor_add', methods =('GET', 'POST'))
@vendor_blueprint.route('/vendor_add/<int:vendor_id>', methods = ('GET', 'POST'))
@login_required
def vendor_add(vendor_id = None):
    from app import mysql
    cur = mysql.connection.cursor()

    if vendor_id:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM vendor WHERE id = %s', (vendor_id,))
        vendor = cur.fetchone()
        
        if request.method == 'POST':
            ct = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            created_by = session.get('username', 'system')
            vendor_name = request.form['vendor_name']
            benefeciery_name = request.form['benefeciery_name']
            address = request.form['address']
            contact_person = request.form['contact_person']
            no_rekening = request.form['no_rekening']
            bank = request.form['bank']
            cur.execute('''
                UPDATE vendor
                SET vendor_name = %s, benefeciery_name = %s, address = %s, contact_person = %s, no_rekening = %s, bank = %s, updated_at = %s, updated_by = %s
                WHERE id = %s
            ''', (vendor_name, benefeciery_name, address, contact_person, no_rekening, bank, ct, created_by, vendor_id))
            mysql.connection.commit()
            flash('Vendor updated successfully', 'success')
            return redirect(url_for('vendor.vendor_list'))
    
    else:
        vendor = []
        if request.method == 'POST':
            ct = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            created_by = session.get('username', 'system')
            vendor_name = request.form['vendor_name']
            benefeciery_name = request.form['benefeciery_name']
            address = request.form['address']
            contact_person = request.form['contact_person']
            no_rekening = request.form['no_rekening']
            bank = request.form['bank']
            cur.execute('''
            INSERT INTO vendor (vendor_name, benefeciery_name, address, contact_person, no_rekening, bank, created_at, created_by, updated_at, updated_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (vendor_name, benefeciery_name, address, contact_person, no_rekening, bank, ct, created_by, ct, created_by))
            mysql.connection.commit()
            flash('Vendor has been added successfully', 'success')
            return redirect(url_for('vendor.vendor_list'))

        cur.close()


    return render_template('vendor/vendor_add.html', vendor=vendor)

# ====================================================================================================================================
# DELETE VENDOR
# ====================================================================================================================================
@vendor_blueprint.route('/delete_vendor/<int:id>',  methods =('GET', 'POST'))
@login_required
def delete_vendor(id):
    from app import mysql
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM vendor WHERE id = %s', (id,))
    mysql.connection.commit()
    cursor.close()
    flash('Vendor has been deleted successfully', 'success')
    # return f'This is Delete id: {id}'
    return redirect(url_for('vendor.vendor_list'))
# ====================================================================================================================================