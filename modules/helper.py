from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from functools import wraps

# LOCK REQUIRED TO LOGIN ==========================================================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('auth.auth', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
# ================================================================================================================


# CHECK ACCESS MENU ==========================================================================================
def check_access(menu_id):
    def decorator(f):
        from app import mysql
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('id')
            if not user_id:
                flash('You need to log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            cursor = mysql.connection.cursor()
            # check user id to access menu
            cursor.execute('SELECT 1 FROM user_access WHERE id_user = %s AND id_menu = %s', (user_id, menu_id))
            access = cursor.fetchone()
            cursor.close()

            if not access:
                # if not error
                flash('You do not have access to this page', 'danger')
                # return abort(403)
                return render_template('forbid.html')
            return f(*args, **kwargs)
        return decorated_function
    return decorator
# ================================================================================================================

def menu_access_required(menu_id):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Cek apakah user memiliki akses ke menu
            if 'menu' not in session or menu_id not in session['menu']:
                # return abort(403)  # Forbidden, jika tidak punya akses
                return render_template('forbid.html')
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# GABUNG =========================================================================================================
# def login_and_check_access(menu_id):
#     def decorator(f):
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             # Check if the user is logged in
#             if 'loggedin' not in session:
#                 next_url = request.url
#                 return redirect(url_for('auth.login', next=next_url))
            
#             user_id = session.get('id')
#             if not user_id:
#                 flash('You need to log in to access this page.', 'warning')
#                 return redirect(url_for('auth.login'))
            
#             # Check access for the logged-in user
#             cursor = mysql.connection.cursor()
#             cursor.execute('SELECT 1 FROM user_access WHERE id_user = %s AND id_menu = %s', (user_id, menu_id))
#             access = cursor.fetchone()
#             cursor.close()

#             if not access:
#                 flash('You do not have access to this page', 'danger')
#                 return abort(403)
            
#             return f(*args, **kwargs)
#         return decorated_function
#     return decorator
# ================================================================================================================