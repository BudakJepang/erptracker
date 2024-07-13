@pr_blueprint.route('/pr_temp_submit', methods=['GET', 'POST'])
def pr_temp_submit():
    pr_number = None

    # Fetch entity and department data from the database
    from app import mysql
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, entity, entity_name FROM entity")
    entities = cursor.fetchall()

    cursor.execute("SELECT id, entity_id, department, department_name FROM department")
    departments = cursor.fetchall()
    
    if request.method == 'POST':

        # VARIABLE PR HEADER
        entity = request.form['entity']
        department = request.form['department']
        no_pr = generate_pr_number(entity, department)
        tanggal_permintaan = request.form['tanggal_permintaan']
        requester_name = 'Mohammad Nurohman'
        total_budget_approved = request.form['total_budget_approved']

        nama_project= request.form['nama_project']
        requester_id = 1
        remarks = ""
        approval1_status = ""
        approval1_user_id = 1
        approval1_notes = ""
        approval2_status = ""
        approval2_user_id = 2
        approval2_notes = ""
        approval3_status = ""
        approval3_user_id = 3
        approval3_notes = ""

        # VARIABLE FOR AUTO_NUM TABLE
        current_date = datetime.now()
        year_month = current_date.strftime('%y%m')

        # INSERT FOR TABLE AUTO NUM
        try:
            cursor.execute("INSERT INTO pr_autonum (entity, department, month, year, pr_no) VALUES (%s, %s, %s, %s, %s)",
                       (entity, department, current_date.month, current_date.year, no_pr))
            mysql.connection.commit()
        except MySQLdb.IntegrityError as e:
            if e.args[0] == 1062:  # Duplicate entry error
                sequence_number = f"{get_next_sequence(entity, department):03d}"
                pr_number = f"PR-{entity}-{department}-{year_month}-{sequence_number}"
                cursor.execute("INSERT INTO pr_autonum (entity, department, month, year, pr_no) VALUES (%s, %s, %s, %s, %s)",
                            (entity, department, current_date.month, current_date.year, pr_number))
                mysql.connection.commit()

        # INSERT TABLE FOR TABLE PR_HEADER
        insert_header_query = '''
                INSERT INTO pr_header (no_pr ,tanggal_permintaan ,requester_id ,requester_name ,nama_project ,entity ,total_budget_approved ,remarks ,approval1_status ,
                approval1_user_id ,approval1_notes ,approval2_status ,approval2_user_id ,approval2_notes ,approval3_status ,approval3_user_id ,approval3_notes ,created_at ,updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        # EXECUTION QUERY FOR TABLE PR_HEADER
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(insert_header_query, (no_pr,tanggal_permintaan ,requester_id ,requester_name ,nama_project ,entity ,total_budget_approved ,remarks ,approval1_status ,
                approval1_user_id ,approval1_notes ,approval2_status ,approval2_user_id ,approval2_notes ,approval3_status ,approval3_user_id ,approval3_notes, today, today))

        items = []
        for i in range(1, len(request.form) // 5 + 1):
            nama_item = request.form[f'nama_item{i}']
            spesifikasi = request.form[f'spesifikasi{i}']
            qty = request.form[f'qty{i}']
            tanggal = request.form[f'tanggal{i}']

            items.append((no_pr, i, nama_item, spesifikasi, qty, tanggal, today, today))

        insert_detail_query = '''
            INSERT INTO pr_detail (no_pr, item_no, nama_item, spesifikasi, qty, tanggal, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''

        cursor.executemany(insert_detail_query, items)
        mysql.connection.commit()
        cursor.close()

    # if request.method == 'POST':
        # entity = request.form['entity']
    #     department = request.form['department']
    #     year_month = datetime.now().strftime('%y%m')
    #     sequence_number = f"{get_next_sequence(entity, department):03d}"

    #     pr_number = f"PR-{entity}-{department}-{year_month}-{sequence_number}"

        # INSERT PR AUTONUM TO TABLE
        # cursor = mysql.connection.cursor()
        # insert_query = '''
        #     INSERT INTO pr_autonum (entity, department, id, month, year, pr_no)
        #     VALUES (%s, %s, %s, %s, %s, %s)
        # '''
        # cursor.execute(insert_query, (entity, department, None, datetime.now().month, datetime.now().year, pr_number))
        # mysql.connection.commit()
        # cursor.close()

    # return render_template('index.html', pr_number=pr_number, entities=entities, departments=departments)

    # if 'pr_request' not in session:
    #     session['pr_request'] = []

    # if request.method == 'POST':
    #     no_pr = request.form['no_pr']
    #     tanggal_permintaan = request.form['tanggal_permintaan']
        # requester_id = request.form['requester_id']
        # requester_name = request.form['requester_name']
        # nama_project = request.form['nama_project']
        # total_budget_approved = request.form['total_budget_approved']
        # remarks = request.form['remarks']
        # approval1_status = request.form['approval1_status']
        # approval1_user_id = request.form['approval1_user_id']
        # approval1_notes = request.form['approval1_notes']
        # approval2_status = request.form['approval2_status']
        # approval2_user_id = request.form['approval2_user_id']
        # approval2_notes = request.form['approval2_notes']
        # approval3_status = request.form['approval3_status']
        # approval3_user_id = request.form['approval3_user_id']
        # approval3_notes = request.form['approval3_notes']
        # created_at = datetime.datetime.strptime(request.form['created_at'], '%Y-%m-%d')
        # updated_at = datetime.datetime.strptime(request.form['updated_at'], '%Y-%m-%d')
        # if no_pr and tanggal_permintaan and requester_name and nama_project and total_budget_approved:
        #     session['pr_request'].append({
        #         'no_pr': no_pr,
        #         'tanggal_permintaan': tanggal_permintaan,
        #         'requester_name': requester_name,
        #         'nama_project': nama_project,
        #         'total_budget_approved': total_budget_approved
        #     })
    return render_template('pr/pr_temp.html', pr_number=pr_number, entities=entities, departments=departments)