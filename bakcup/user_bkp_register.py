# REGISTRATION AND ACCESS USER
@user_blueprint.route('/register', methods=('GET', 'POST'))
@login_required
def register():
    from app import mysql
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        level = request.form['level']
        selected_menus = request.form.getlist('menus')  # ambil daftar menu yang dipilih dari view html

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT username, email FROM user_accounts WHERE username=%s OR email=%s', (username, email))
        account = cursor.fetchone()
        
        if account is None:
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            created_by = session.get('username', 'system')  # get the username of the logged in user or 'system'
            cursor.execute('''
                INSERT INTO user_accounts (username, email, password, level, created_at, updated_at, created_by, updated_by) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (username, email, generate_password_hash(password), level, current_timestamp, current_timestamp, created_by, created_by))
            mysql.connection.commit()
            user_id = cursor.lastrowid  # get ID user yang baru saja dibuat

            # simpan data menu yang dipilih ke tabel access_users
            for menu_id in selected_menus:
                cursor.execute('''
                    INSERT INTO access_users (id_user, id_menu, created_at, updated_at, created_by, updated_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (user_id, menu_id, current_timestamp, current_timestamp, created_by, created_by))
            
            mysql.connection.commit()
            cursor.close()
            flash('Registration Success', 'success')
            return redirect(url_for('user.user_list'))
        else:
            cursor.close()
            flash('Username or Email already exists', 'danger')
            return redirect(url_for('user.user_list'))
    return render_template('users/user_add.html')