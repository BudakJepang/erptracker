from flask import redirect, url_for, flash, session, abort
from functools import wraps

# LOCK REQUIRED TO LOGIN
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('auth.auth'))
        return f(*args, **kwargs)
    return decorated_function

def check_access(menu_id):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('id')
            if not user_id:
                return redirect(url_for('login'))

            cursor = mysql.connection.cursor()
            cursor.execute('SELECT 1 FROM access_users WHERE user_id = %s AND menu_id = %s', (user_id, menu_id))
            access = cursor.fetchone()
            cursor.close()

            if not access:
                flash('You do not have access to this page', 'warning')
                return abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
