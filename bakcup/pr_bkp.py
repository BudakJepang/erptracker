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


    # PR BACKUP NEW AFTER ALTER TABLE OR ADD TABLE APPROVAL
    from flask import Blueprint, redirect, render_template, request, session, url_for, flash, jsonify, current_app
import os
from werkzeug.security import check_password_hash, generate_password_hash
from modules.time import convert_time_to_wib
from datetime import datetime, timedelta, timezone
from modules.decorator import login_required, check_access
from functools import wraps
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
from flask_mysqldb import MySQL, MySQLdb
from werkzeug.utils import secure_filename
from modules.mail import pr_mail



# ====================================================================================================================================
# PR UTILITES
# ====================================================================================================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('auth.auth'))
        return f(*args, **kwargs)
    return decorated_function


# BLUEPRINT AUTH VARIABLE
pr_blueprint = Blueprint('pr', __name__)
# ====================================================================================================================================


# ====================================================================================================================================
# PR MAIN LIST
# ====================================================================================================================================
@pr_blueprint.route('/pr_list')
def pr_list():
    from app import mysql
    import traceback
    
    user_id = session.get('id', 'system')
    if user_id == 'system':
        return redirect(url_for('login'))  # Redirect to login if session is not set

    try:
        cursor = mysql.connection.cursor()
        query = '''
        SELECT DISTINCT
            ph.no_pr,
            ph.tanggal_permintaan,
            ph.requester_id,
            ph.requester_name,
            ph.nama_project,
            ph.entity_id,
            e.entity_name,
            ph.total_budget_approved,
            ph.remarks,
            ph.approval1_status,
            ph.approval1_user_id,
            ph.approval1_notes,
            ua1.username AS approval1_username,
            ph.approval2_status,
            ph.approval2_user_id,
            ph.approval2_notes,
            ua2.username AS approval2_username,
            ph.approval3_status,
            ph.approval3_user_id,
            ph.approval3_notes,
            ua3.username AS approval3_username,
            SUM(pd.qty) AS total_qty
        FROM pr_header ph
        LEFT JOIN pr_detail pd ON ph.no_pr = pd.no_pr
        LEFT JOIN user_accounts ua1 ON ph.approval1_user_id = ua1.id
        LEFT JOIN user_accounts ua2 ON ph.approval2_user_id = ua2.id
        LEFT JOIN user_accounts ua3 ON ph.approval3_user_id = ua3.id
        LEFT JOIN entity e ON ph.entity_id = e.id
        WHERE ph.entity_id IN (
            SELECT DISTINCT entity_id 
            FROM user_entity 
            WHERE user_id = %s
        )
        AND (ph.requester_id = %s  OR ph.approval1_user_id = %s OR ph.approval2_user_id = %s OR ph.approval3_user_id = %s)
        GROUP BY ph.no_pr, ph.tanggal_permintaan, ph.requester_id, ph.requester_name, 
                 ph.nama_project, ph.entity_id, e.entity_name, ph.total_budget_approved, 
                 ph.remarks, ph.approval1_status, ph.approval1_user_id, ph.approval1_notes, 
                 ua1.username, ph.approval2_status, ph.approval2_user_id, ph.approval2_notes, 
                 ua2.username, ph.approval3_status, ph.approval3_user_id, ph.approval3_notes, 
                 ua3.username
        ORDER BY ph.tanggal_permintaan DESC, ph.no_pr DESC
        '''
        cursor.execute(query, (user_id, user_id, user_id, user_id, user_id))
        data = cursor.fetchall()
    except Exception as e:
        traceback.print_exc()  # Print stack trace for debugging
        return "An error occurred while fetching the PR list."
    finally:
        cursor.close()
    
    return render_template('pr/pr_list.html', data=data)

# ====================================================================================================================================


# ====================================================================================================================================
# PR GENERATE PDF TEMP
# ====================================================================================================================================
@pr_blueprint.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    no_pr = request.form.get('no_pr')
    from app import mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM purchase_requisition WHERE no_pr = %s", (no_pr,))
    pr = cur.fetchone()
    cur.close()

    if not pr:
        return "PR not found", 404

    # Parse dates
    created_at = pr[17] if pr[17] else None
    if isinstance(created_at, str):
        created_at = datetime.datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
    due_date = pr[10] if pr[10] else None
    if isinstance(due_date, str):
        due_date = datetime.datetime.strptime(due_date, '%Y-%m-%d')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    centered_style = ParagraphStyle(name='centered', alignment=TA_CENTER, fontSize=12, fontName='Helvetica')
    title_style = ParagraphStyle(name='title', alignment=TA_CENTER, fontSize=20, fontName='Helvetica-Bold')
    table_content_style = ParagraphStyle(name='table_content', alignment=TA_CENTER, fontSize=11)
    table_content_style_left = ParagraphStyle(name='table_content_left', alignment=TA_LEFT, fontSize=11)
    table_header_style = ParagraphStyle(name='table_header', alignment=TA_CENTER, fontSize=11, fontName='Helvetica-Bold')
    footer_style = ParagraphStyle(name='footer', fontSize=11, fontName='Helvetica-Bold')
    name_footer_style = ParagraphStyle(name='footer', fontSize=11, fontName='Helvetica-Bold',  alignment=TA_CENTER)
    detail_key_style = ParagraphStyle(name='detail_key', fontSize=11, fontName='Helvetica-Bold')
    detail_value_style = ParagraphStyle(name='detail_value', fontSize=11)

    # Add logo
    # logo_path = 'unnamed.png'  # Update this with the correct path to your logo
    # logo = Image(logo_path, 0.7*inch, 0.7*inch)  # Adjust width and height as needed
    # logo.hAlign = 'LEFT'  # Align the logo to the left
    # elements.append(logo)
    # elements.append(Spacer(1, 12))
    # elements.append(Spacer(1, 12))

    # Title
    title = Paragraph('Purchase Requisition (PR)', title_style)
    elements.append(title)
    elements.append(Spacer(1, 15))

    # PR Number
    pr_number = Paragraph(f'(Form Permintaan Barang / Jasa)', centered_style)
    elements.append(pr_number)
    elements.append(Spacer(1, 11))
    pr_number = Paragraph(f'No. PR: {pr[1]}', centered_style)
    elements.append(pr_number)
    elements.append(Spacer(1, 11))

    # Details
    detail_data = [
        [Paragraph('', detail_key_style), Paragraph('', footer_style)],
        [Paragraph('Tanggal Permintaan', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{created_at.strftime("%d %B %Y") if created_at else "N/A"}', detail_value_style)],
        [Paragraph('User / Requester', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{pr[2]}', detail_value_style)],
        [Paragraph('Nama Project', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{pr[3]}', detail_value_style)],
        [Paragraph('Sumber Budget / Entyty', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{pr[4]}', detail_value_style)],
        [Paragraph('Total Budget Approved', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'Rp. {pr[5]:,.2f} (PPN Exclude)', detail_value_style)],
        [Paragraph('', detail_key_style), Paragraph('', footer_style)]
    ]

    table_detail = Table(detail_data, colWidths=[3.9*inch, 0.2*inch, 2.8*inch])
    table_detail.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    elements.append(table_detail)
    elements.append(Spacer(1, 12))

    # Table
    # item_description = Paragraph(pr[7], ParagraphStyle(name='item_description', wordWrap='CJK', alignment=TA_LEFT, fontSize=11))
    item_description = Paragraph(pr[7], ParagraphStyle(name='item_description', alignment=TA_LEFT, fontSize=11, wordWrap='CJK'))


    table_data = [
        [Paragraph('No', table_header_style), Paragraph('Nama Barang/Jasa', table_header_style), 
         Paragraph('Spesifikasi Barang/Jasa', table_header_style), Paragraph('QTY', table_header_style), 
         Paragraph('Tanggal dibutuhkan', table_header_style)],
        [Paragraph('1', table_content_style), Paragraph(pr[6], table_content_style), item_description, 
         Paragraph(str(pr[8]), table_content_style), 
         Paragraph(due_date.strftime('%d %b %Y') if due_date else 'N/A', table_content_style)]
    ]

    table = Table(table_data, colWidths=[0.5*inch, 1.5*inch, 3*inch, 0.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align content to the top
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    # Footer with digital signature
    tanda_tangan_path = 'ttn.png'  # Update with the path to your digital signature image
    tanda_tangan = Image(tanda_tangan_path, width=1.1*inch, height=0.60*inch)
    table_footer_data = [
        [Paragraph('', footer_style), Paragraph('', footer_style)],
        [Paragraph('Dibuat Oleh', name_footer_style), Paragraph('', name_footer_style), Paragraph('      Disetujui Oleh', name_footer_style)],
        [tanda_tangan,tanda_tangan,tanda_tangan, Paragraph('', footer_style)],
        [Paragraph(f'({pr[11]})', name_footer_style), Paragraph(f'({pr[12]})', name_footer_style), Paragraph(f'({pr[13]})', name_footer_style), Paragraph(f'({pr[14]})', name_footer_style), Paragraph(f'({pr[15]})', name_footer_style)]
    ]
    

    # table_footer_data = [
    #     [Paragraph('Dibuat Oleh', footer_style), tanda_tangan, Paragraph('      Disetujui Oleh', footer_style)],
    #     [Paragraph('', footer_style), Paragraph('', footer_style), Paragraph('', footer_style)],
    #     [Paragraph(f'({pr[10]})', footer_style), Paragraph(f'({pr[11]})', footer_style), Paragraph(f'({pr[12]})', footer_style), Paragraph(f'({pr[13]})', footer_style), Paragraph(f'({pr[14]})', footer_style)]
    # ]

    table_footer = Table(table_footer_data, colWidths=[2.1*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
    table_footer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    elements.append(table_footer)
    elements.append(Spacer(1, 12))

    doc.build(elements)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='purchase_requisition.pdf', mimetype='application/pdf')
# ====================================================================================================================================


# ====================================================================================================================================
# PR FORM SUBMIT
# ====================================================================================================================================

# GET SEQUENCE PR AUTONUMBER
def get_next_sequence(entity, department):
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    from app import mysql

    cursor = mysql.connection.cursor()
    query = '''
        SELECT pr_no FROM pr_autonum
        WHERE entity = %s AND department = %s AND month = %s AND year = %s
        ORDER BY created_at DESC LIMIT 1
    '''
    cursor.execute(query, (entity, department, current_month, current_year))
    last_pr = cursor.fetchone()

    if last_pr:
        last_sequence_number = int(last_pr[0].split('-')[-1])
        next_sequence_number = last_sequence_number + 1
    else:
        next_sequence_number = 1

    cursor.close()
    return next_sequence_number


# EXTRACT AND JOIN PR AUTONUMBER BY DATE
def generate_pr_number(entity, department):
    current_date = datetime.now()
    year_month = current_date.strftime('%y%m')
    sequence_number = f"{get_next_sequence(entity, department):03d}"
    pr_number = f"PR-{entity}-{department}-{year_month}-{sequence_number}"
    return pr_number


# EXTRACT AND JOIN PR AUTONUMBER BY DATE
@pr_blueprint.route('/generate_pr', methods=['GET', 'POST'])
def generate_pr():
    data = request.json
    entity = data['entity']
    department = data['department']
    pr_number = generate_pr_number(entity, department)
    return jsonify({'pr_number': pr_number})


# MAIN PR SUBMIT 
@pr_blueprint.route('/pr_temp_submit', methods=['GET', 'POST'])
def pr_temp_submit():
    pr_number = None

    # GET ENTITY AND DEPARTMENT
    from app import mysql

    # get user by entities form session
    user_entities = session.get('entities', [])

    # convert entities to list id if user have access more than 1 entity
    entity_ids = [entity['entity_id'] for entity in user_entities]
    cursor = mysql.connection.cursor()

    if entity_ids:
        cursor.execute("SELECT id, entity, entity_name FROM entity WHERE id IN %s", (tuple(entity_ids),))
        entities = cursor.fetchall()
    else:
        entities = []

    # get department list
    cursor.execute("SELECT id, entity_id, department, department_name FROM department WHERE entity_id = 1")
    departments = cursor.fetchall()

    # get approval list
    cursor.execute("SELECT id, username, email FROM user_accounts WHERE level = 4")
    approver = cursor.fetchall()
    
    if request.method == 'POST':
        # VARIABLE PR HEADER
        entity = request.form['entity']
        department = request.form['department']
        no_pr = generate_pr_number(entity, department)
        tanggal_permintaan = request.form['tanggal_permintaan']
        requester_name = session.get('username', 'system')  # get the username from session auth
        requester_id = session.get('id', 'system')  # get id user from session auth
        total_budget_approved = request.form['total_budget_approved']
        nama_project = request.form['nama_project']
        remarks = None

        # get approval value from form PR_HEADER
        approval1_user_id = request.form.get('approval1_user_id', None)
        approval2_user_id = request.form.get('approval2_user_id', None)
        approval3_user_id = request.form.get('approval3_user_id', None)

        # approval condition jika datanya isi atau null
        approval1_user_id = approval1_user_id if approval1_user_id else None
        approval2_user_id = approval2_user_id if approval2_user_id else None
        approval3_user_id = approval3_user_id if approval3_user_id else None
        approval1_status = None
        approval1_notes = None
        approval2_status = None
        approval2_notes = None
        approval3_status = None
        approval3_notes = None

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

        # ADD CONDITION FOR INSERT TO DB BY entity_id
        if entity == 'CNI':
            entity = 1
        elif entity == 'OID':
            entity = 2
        elif entity == 'RKI':
            entity = 3
        elif entity == 'DMI':
            entity = 4
        elif entity == 'AGI':
            entity = 5
        elif entity == 'OPN':
            entity = 6
        elif entity == 'ATI':
            entity = 7
        elif entity == 'AMP':
            entity = 8
        elif entity == 'TKM':
            entity = 9
        else:
            entity = None

        # INSERT TABLE FOR TABLE PR_HEADER
        insert_header_query = '''
                INSERT INTO pr_header (no_pr ,tanggal_permintaan ,requester_id ,requester_name ,nama_project ,entity_id,total_budget_approved ,remarks ,approval1_status ,
                approval1_user_id ,approval1_notes ,approval2_status ,approval2_user_id ,approval2_notes ,approval3_status ,approval3_user_id ,approval3_notes ,created_at ,updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''

        # EXECUTION QUERY FOR TABLE PR_HEADER
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(insert_header_query, (no_pr, tanggal_permintaan, requester_id, requester_name, nama_project, entity, total_budget_approved, remarks, approval1_status,
                                             approval1_user_id, approval1_notes, approval2_status, approval2_user_id, approval2_notes, approval3_status, approval3_user_id, approval3_notes, today, today))
        mysql.connection.commit()

        
        # PROVISIONING INSERT TO TABLE PR_DETAIL
        items = []
        index = 1
        while True:
            try:
                nama_item = request.form[f'nama_item{index}']
                spesifikasi = request.form[f'spesifikasi{index}']
                qty = request.form[f'qty{index}']
                tanggal = request.form[f'tanggal{index}']
                items.append((no_pr, index, nama_item, spesifikasi, qty, tanggal, today, today))
                index += 1
            except KeyError:
                break

        if items:
            insert_detail_query = '''
                INSERT INTO pr_detail (no_pr, item_no, nama_item, spesifikasi, qty, tanggal, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.executemany(insert_detail_query, items)
            mysql.connection.commit()


        # HANDLE FILE UPLOADS
        upload_files = request.files.getlist('files[]')
        upload_docs = []
        for i, file in enumerate(upload_files):
            if file:
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(upload_path)
                upload_docs.append((no_pr, filename, upload_path, requester_id, today, requester_id, today))

        if upload_docs:
            insert_docs_query = '''
                INSERT INTO pr_docs_reference (no_pr, doc_name, path, created_by, created_at, updated_by, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.executemany(insert_docs_query, upload_docs)
            mysql.connection.commit()
        
        cursor.close()
        # pr_mail(no_pr, entity, department, nama_project, tanggal_permintaan, total_budget_approved, tanggal, approval2_user_id)
        flash('New PR has been added', 'success')

        return redirect(url_for('pr.pr_list'))
    return render_template('pr/pr_temp.html', pr_number=pr_number, entities=entities, departments=departments, approver=approver)
# ==========================================================================================================================================


# @pr_blueprint.route('/pr_detail_page', methods=['GET', 'POST'])
# def pr_detail_page():
#     return render_template('pr/pr_detail.html')

import logging

# Set up logging
# logging.basicConfig(level=logging.DEBUG)

# PT DETAIL
@pr_blueprint.route('/pr_detail_page/<no_pr>', methods=['GET', 'POST'])
def pr_detail_page(no_pr):
    from app import mysql
    cur = mysql.connection.cursor()
    query = """
            SELECT 
            DISTINCT
                ph.no_pr,
                ph.tanggal_permintaan,
                ph.requester_id,
                ph.requester_name,
                ph.nama_project,
                ph.entity_id,
                ph.total_budget_approved,
                ph.remarks,
                ph.approval1_status,
                ph.approval1_user_id,
                ph.approval1_notes,
                ua1.username as approval1_username,
                ph.approval2_status,
                ph.approval2_user_id,
                ph.approval2_notes,
                ua2.username as approval2_username,
                ph.approval3_status,
                ph.approval3_user_id,
                ph.approval3_notes,
                ua3.username as approval3_username,
                pd.item_no,
                pd.nama_item,
                pd.spesifikasi,
                pd.qty,
                pd.tanggal,
                pdr.doc_name,
                e.entity,
                e.entity_name,
                pdr.path
            FROM pr_header ph
            LEFT JOIN pr_detail pd 
            ON ph.no_pr=pd.no_pr
            LEFT JOIN pr_docs_reference pdr 
            ON ph.no_pr =pdr.no_pr 
            LEFT JOIN user_accounts ua1 
            ON ph.approval1_user_id =ua1.id 
            LEFT JOIN user_accounts ua2
            ON ph.approval2_user_id =ua2.id 
            LEFT JOIN user_accounts ua3
            ON ph.approval3_user_id =ua3.id 
            LEFT JOIN entity e 
            ON ph.entity_id = e.id
            WHERE ph.no_pr = %s
            ORDER BY tanggal_permintaan, no_pr DESC
    """
    cur.execute(query, [no_pr])
    data = cur.fetchall()
    cur.close()
    
    current_user_id = session.get('id', 'system')
    print(current_user_id)
    
    # Log data for debugging
    logging.debug(f"Data fetched for no_pr {no_pr}: {data}")
    
    return render_template('pr/pr_detail.html', data=data, current_user_id=current_user_id)


# PR APPROVED
@pr_blueprint.route('/pr_approved/<no_pr>', methods=['GET', 'POST'])
def pr_approved(no_pr):
    from app import mysql
    cur = mysql.connection.cursor()
    current_user_id = session.get('id', 'system')


    if request.method == 'POST':
        approval_notes = request.form.get('spesifikasi1')
        approval_user_id = current_user_id 
        
        if approval_user_id == 7:  
            status_column = 'approval1_status'
            notes_column = 'approval1_notes'
            user_id_column = 'approval1_user_id'
        elif approval_user_id == 2: 
            status_column = 'approval2_status'
            notes_column = 'approval2_notes'
            user_id_column = 'approval2_user_id'
        elif approval_user_id == 3:
            status_column = 'approval3_status'
            notes_column = 'approval3_notes'
            user_id_column = 'approval3_user_id'
        else:
            flash('User tidak memiliki hak untuk mengapprove PR ini', 'danger')
            return redirect(url_for('pr.pr_list'))

        # Update query
        update_query = f"""
            UPDATE pr_header
            SET {status_column} = 'APPROVED',
                {notes_column} = %s,
                updated_at = NOW()
            WHERE no_pr = %s AND {user_id_column} = %s
        """

        try:
            cur.execute(update_query, (approval_notes, no_pr, approval_user_id))
            mysql.connection.commit()
            flash('PR has been approved successfully!', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error: {str(e)}', 'danger')
        finally:
            cur.close()
    
    return redirect(url_for('pr.pr_list')) 


# PR EDIT BAKCUP 
@pr_blueprint.route('/pr_edit/<no_pr>', methods=['GET', 'POST'])
def pr_edit(no_pr):
    from app import mysql

    # GET ENTITY AND DEPARTMENT
    user_entities = session.get('entities', [])
    entity_ids = [entity['entity_id'] for entity in user_entities]
    cursor = mysql.connection.cursor()

    if entity_ids:
        cursor.execute("SELECT id, entity, entity_name FROM entity WHERE id IN %s", (tuple(entity_ids),))
        entities = cursor.fetchall()
    else:
        entities = []

    cursor.execute("SELECT id, entity_id, department, department_name FROM department WHERE entity_id = 1")
    departments = cursor.fetchall()

    cursor.execute("SELECT id, username, email FROM user_accounts WHERE level = 4")
    approver = cursor.fetchall()

    if request.method == 'POST':
        # PR HEADER VARIABLES
        entity = request.form['entity']
        department = request.form['department']
        tanggal_permintaan = request.form['tanggal_permintaan']
        requester_name = session.get('username', 'system')
        requester_id = session.get('id', 'system')
        total_budget_approved = request.form['total_budget_approved']
        nama_project = request.form['nama_project']
        remarks = None

        # ADD CONDITION FOR ENTITY ID
        entity_map = {
            'CNI': 1, 'OID': 2, 'RKI': 3, 'DMI': 4, 'AGI': 5,
            'OPN': 6, 'ATI': 7, 'AMP': 8, 'TKM': 9
        }
        entity_id = entity_map.get(entity, None)

        # UPDATE TABLE PR_HEADER
        update_header_query = '''
            UPDATE pr_header 
            SET tanggal_permintaan = %s, requester_id = %s, requester_name = %s, 
                nama_project = %s, entity_id = %s, total_budget_approved = %s, remarks = %s, updated_at = %s
            WHERE no_pr = %s
        '''
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(update_header_query, (tanggal_permintaan, requester_id, requester_name, nama_project, entity_id, total_budget_approved, remarks, today, no_pr))
        mysql.connection.commit()

        # UPDATE TABLE PR_APPROVAL
        delete_approval_query = "DELETE FROM pr_approval WHERE no_pr = %s"
        cursor.execute(delete_approval_query, (no_pr,))
        mysql.connection.commit()

        approval_list = []
        idx = 1
        while True:
            try:
                approval_user_id = request.form[f'approval_user_id{idx}']
                approval_list.append((no_pr, approval_user_id, None, None, today))
                idx += 1
            except KeyError:
                break

        if approval_list:
            insert_approval_query = '''
                INSERT INTO pr_approval (no_pr, approval_user_id, status, notes, created_at)
                VALUES (%s, %s, %s, %s, %s)
            '''
            cursor.executemany(insert_approval_query, approval_list)
            mysql.connection.commit()

        # UPDATE TABLE PR_DETAIL
        delete_detail_query = "DELETE FROM pr_detail WHERE no_pr = %s"
        cursor.execute(delete_detail_query, (no_pr,))
        mysql.connection.commit()

        items = []
        index = 1
        while True:
            try:
                nama_item = request.form[f'nama_item{index}']
                spesifikasi = request.form[f'spesifikasi{index}']
                qty = request.form[f'qty{index}']
                tanggal = request.form[f'tanggal{index}']
                items.append((no_pr, index, nama_item, spesifikasi, qty, tanggal, today, today))
                index += 1
            except KeyError:
                break

        if items:
            insert_detail_query = '''
                INSERT INTO pr_detail (no_pr, item_no, nama_item, spesifikasi, qty, tanggal, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.executemany(insert_detail_query, items)
            mysql.connection.commit()

        # HANDLE FILE UPLOADS
        upload_files = request.files.getlist('files[]')
        upload_docs = []
        for i, file in enumerate(upload_files):
            if file:
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(upload_path)
                upload_docs.append((no_pr, filename, upload_path, requester_id, today, requester_id, today))

        if upload_docs:
            delete_docs_query = "DELETE FROM pr_docs_reference WHERE no_pr = %s"
            cursor.execute(delete_docs_query, (no_pr,))
            mysql.connection.commit()

            insert_docs_query = '''
                INSERT INTO pr_docs_reference (no_pr, doc_name, path, created_by, created_at, updated_by, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.executemany(insert_docs_query, upload_docs)
            mysql.connection.commit()

        cursor.close()
        flash('PR has been updated', 'success')
        return redirect(url_for('pr.pr_list'))

    # FETCH EXISTING PR DATA
    cursor.execute("SELECT * FROM pr_header WHERE no_pr = %s", (no_pr,))
    pr_header = cursor.fetchone()

    cursor.execute("SELECT * FROM pr_detail WHERE no_pr = %s", (no_pr,))
    pr_details = cursor.fetchall()

    cursor.execute("SELECT * FROM pr_approval WHERE no_pr = %s", (no_pr,))
    pr_approvals = cursor.fetchall()

    return render_template('pr/pr_edit.html', pr_header=pr_header, pr_details=pr_details, pr_approvals=pr_approvals, entities=entities, departments=departments, approver=approver)


# DELETE ID BY DETAIL

# Mengambil data lama dari database
cur.execute("SELECT id FROM pr_detail WHERE no_pr = %s", (no_pr,))
old_details = cur.fetchall()
old_ids = {detail[0] for detail in old_details}

# Membuat set ID baru berdasarkan panjang detail dari form
new_ids = set(range(1, len(details) + 1))

cur.execute("SELECT id FROM pr_detail WHERE no_pr = %s", (no_pr,))
old_details = cur.fetchall()
old_ids = {detail[0] for detail in old_details}

# Membuat set ID baru berdasarkan panjang detail dari form
new_ids = set(range(1, len(details) + 1))

# Menghapus row yang dihapus dari form
to_delete = old_ids - new_ids
for del_id in to_delete:
cur.execute("DELETE FROM pr_detail WHERE no_pr = %s AND id = %s", (no_pr, del_id))


# REQUESTER AND APPROVAL SIGN LOGIC
 # GET DIGITAL SIGNATURE FROM DATABASE
    signature_path = requester_sign
    signature_image = Image(signature_path, width=50, height=50)

    signature_row = [signature_image]

    # PR APPROVAL
    table_footer_data = [
        [Paragraph('Dibuat Oleh', footer_style), Paragraph('      Disetujui Oleh', footer_style)]
    ]

    # SPACING
    for x in range(1):
        table_footer_data.append([Paragraph('', footer_style), Paragraph('', footer_style), Paragraph('', footer_style)])

    # ADD NAMES APPROVAL HORIZONTAL
    approval_row = [
        [Paragraph(f'({pr_header[3]})', footer_style)]
        ]

    for approval in pr_approval:
        approval_row.append([Paragraph(f'{approval[6]}', footer_style), Paragraph(f'({approval[3]})', footer_style)])
        signHand = approval[7]
        if not signHand:
            signHand = 'static/uploads/white.png'

        signature_row.append(Image(signHand, width=50, height=50)) 


    # MAKESURE REQUIRED NUMBER
    while len(approval_row) < 3:
        approval_row.append([Paragraph('', footer_style)])
        signature_row.append(Paragraph('', footer_style))

    table_footer_data.append(signature_row)
    table_footer_data.append(approval_row)

    table_footer = Table(table_footer_data, colWidths=[2.1 * inch, 2.0 * inch, 2.0 * inch])
    table_footer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))

    elements.append(table_footer)
    elements.append(Spacer(1, 12))

 # TESTER MERGE PDF
    # Read the main document PDF
    from PyPDF2 import PdfReader, PdfWriter
    main_pdf = PdfReader(buffer)
    # Query to get additional file paths
    cur.execute('''
        SELECT path
        FROM pr_docs_reference pdr 
        WHERE no_pr = %s
    ''', (no_pr, ))

    # additional_paths = [row[0] for row in cur.fetchall()]
   # Path to additional files
    additional_paths = ['uploads/luffy.jpeg']  # Change this to a list of your paths

    # Create a PdfWriter object
    pdf_writer = PdfWriter()

    # Add all pages from the main PDF
    for page_num in range(len(main_pdf.pages)):
        pdf_writer.add_page(main_pdf.pages[page_num])

    # Function to convert JPG/JPEG to PDF
    def convert_image_to_pdf(image_path):
        try:
            img_buffer = BytesIO()
            img_doc = SimpleDocTemplate(img_buffer, pagesize=A4)
            elements = []

            # Create an Image object
            img = Image(image_path)
            img_width, img_height = img.wrap(0, 0)

            # Calculate scaling to fit the image into A4 size
            scale = min(A4[0] / img_width, A4[1] / img_height)
            img.drawWidth = img_width * scale
            img.drawHeight = img_height * scale

            # Add the scaled image to the elements list
            elements.append(img)
            
            img_doc.build(elements)
            img_buffer.seek(0)
            print(f"Converted image {image_path} to PDF successfully.")
            return img_buffer
        except Exception as e:
            print(f"Error converting image to PDF: {e}")
            return None

    # Add all pages from the additional files
    for path in additional_paths:
        print(f"Processing file: {path}")
        if path.endswith('.pdf'):
            try:
                with open(path, "rb") as f:
                    additional_pdf = PdfReader(f)
                    for page_num in range(len(additional_pdf.pages)):
                        pdf_writer.add_page(additional_pdf.pages[page_num])
                print(f"Added pages from PDF file: {path}")
            except Exception as e:
                print(f"Error adding PDF file {path}: {e}")
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            image_pdf_buffer = convert_image_to_pdf(path)
            if image_pdf_buffer:
                image_pdf = PdfReader(image_pdf_buffer)
                for page_num in range(len(image_pdf.pages)):
                    pdf_writer.add_page(image_pdf.pages[page_num])
                print(f"Added pages from image file: {path}")
            else:
                print(f"Skipping invalid image file: {path}")

    # Write the combined PDF to a new buffer
    combined_buffer = BytesIO()
    pdf_writer.write(combined_buffer)
    combined_buffer.seek(0)

    print("Combined PDF generated successfully.")

# SIGNATURE ROW
    signature_row = [signature_image]
    date_row = [Paragraph('', footer_style)]
    approval_row = [Paragraph(f'({pr_header[3]})', footer_style)]

    # Menambahkan tanda tangan persetujuan, tanggal persetujuan, dan nama
    for approval in pr_approval:
        approval_date = str(approval[6]) if approval[6] else ''
        approval_name = f'({approval[3]})' if approval[3] else ''
        sign_path = approval[7] if approval[7] else 'static/uploads/white.png'

        # Tanda tangan
        signature_row.append(Image(sign_path, width=50, height=50))
        
        # Tanggal persetujuan
        date_row.append(Paragraph(approval_date, footer_style))
        
        # Nama persetujuan
        approval_row.append(Paragraph(approval_name, footer_style))

    # Menambahkan baris kosong jika kolom kurang dari 3
    while len(approval_row) < 3:
        signature_row.append(Paragraph('', footer_style))
        date_row.append(Paragraph('', footer_style))
        approval_row.append(Paragraph('', footer_style))

    # Menambahkan baris tanda tangan, tanggal, dan nama ke dalam data footer tabel
    table_footer_data.append(signature_row)
    table_footer_data.append(date_row)
    table_footer_data.append(approval_row)

    # Membuat tabel footer
    table_footer = Table(table_footer_data, colWidths=[2.1 * inch, 2.0 * inch, 2.0 * inch])
    table_footer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))

    # Menambahkan tabel footer ke dalam elemen dokumen
    elements.append(table_footer)
    elements.append(Spacer(1, 12))

# PR LIST QUERY ==============================================
query = '''SELECT 
    ph.no_pr,
    DATE(ph.tanggal_permintaan) tanggal_permintaan,
    ph.requester_id,
    ph.requester_name,
    ph.nama_project,
    ph.entity_id,
    e.entity_name,
    ph.total_budget_approved,
    ph.remarks,
    ph.created_at,
    pa.status
FROM pr_header ph
LEFT JOIN pr_detail pd ON ph.no_pr = pd.no_pr 
LEFT JOIN (
    SELECT pa1.no_pr, pa1.status, pa1.approval_user_id
    FROM pr_approval pa1
    INNER JOIN (
        SELECT no_pr, MAX(approval_no) as max_approval_no
        FROM pr_approval
        GROUP BY no_pr
    ) pa2 ON pa1.no_pr = pa2.no_pr AND pa1.approval_no = pa2.max_approval_no
) pa ON ph.no_pr = pa.no_pr
LEFT JOIN entity e ON ph.entity_id = e.id
WHERE ph.entity_id IN (
    SELECT DISTINCT entity_id
    FROM user_entity 
    WHERE user_id = 1
)
AND (ph.requester_id = 1 OR pa.approval_user_id = 1)
AND ph.no_pr = 'PR-CNI-TCH-2408-001';'''


# BACKUP 2024-08-12
# ====================================================================================================================================
# PR FORM SUBMIT
# ====================================================================================================================================
# GET SEQUENCE PR AUTONUMBER
def get_next_sequence(entity, department):
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    from app import mysql

    cursor = mysql.connection.cursor()
    query = '''
        SELECT pr_no FROM pr_autonum
        WHERE entity = %s AND department = %s AND month = %s AND year = %s
        ORDER BY created_at DESC LIMIT 1
    '''
    cursor.execute(query, (entity, department, current_month, current_year))
    last_pr = cursor.fetchone()

    if last_pr:
        last_sequence_number = int(last_pr[0].split('-')[-1])
        next_sequence_number = last_sequence_number + 1
    else:
        next_sequence_number = 1

    cursor.close()
    return next_sequence_number


# EXTRACT AND JOIN PR AUTONUMBER BY DATE
def generate_pr_number(entity, department):
    current_date = datetime.now()
    year_month = current_date.strftime('%y%m')
    sequence_number = f"{get_next_sequence(entity, department):03d}"
    pr_number = f"PR-{entity}-{department}-{year_month}-{sequence_number}"
    return pr_number


# EXTRACT AND JOIN PR AUTONUMBER BY DATE
@pr_blueprint.route('/generate_pr', methods=['GET', 'POST'])
def generate_pr():
    data = request.json
    entity = data['entity']
    department = data['department']
    pr_number = generate_pr_number(entity, department)
    return jsonify({'pr_number': pr_number})


# MAIN PR SUBMIT_________________________________________________________________
@pr_blueprint.route('/pr_temp_submit', methods=['GET', 'POST'])
@login_required
def pr_temp_submit():
    pr_number = None

    # GET ENTITY AND DEPARTMENT
    from app import mysql

    # get user by entities form session
    user_entities = session.get('entities', [])

    # convert entities to list id if user have access more than 1 entity
    entity_ids = [entity['entity_id'] for entity in user_entities]
    cursor = mysql.connection.cursor()

    if entity_ids:
        cursor.execute("SELECT id, entity, entity_name FROM entity WHERE id IN %s", (tuple(entity_ids),))
        entities = cursor.fetchall()
    else:
        entities = []

    # get department list
    cursor.execute("SELECT id, entity_id, department, department_name FROM department WHERE entity_id = 1")
    departments = cursor.fetchall()

    # get approval list
    cursor.execute("SELECT id, username, email FROM user_accounts WHERE level = 4")
    approver = cursor.fetchall()
    
    if request.method == 'POST':
        # VARIABLE PR HEADER
        entity = request.form['entity']
        department = request.form['department']
        no_pr = generate_pr_number(entity, department)
        tanggal_permintaan = request.form['tanggal_permintaan']
        requester_name = session.get('username', 'system')  # get the username from session auth
        requester_id = session.get('id', 'system')  # get id user from session auth
        total_budget_approved = request.form['total_budget_approved']
        nama_project = request.form['nama_project']
        remarks = None

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

        # ADD CONDITION FOR INSERT TO DB BY entity_id
        if entity == 'CNI':
            entity = 1
        elif entity == 'OID':
            entity = 2
        elif entity == 'RKI':
            entity = 3
        elif entity == 'DMI':
            entity = 4
        elif entity == 'AGI':
            entity = 5
        elif entity == 'OPN':
            entity = 6
        elif entity == 'ATI':
            entity = 7
        elif entity == 'AMP':
            entity = 8
        elif entity == 'TKM':
            entity = 9
        else:
            entity = None

        # INSERT INTO TABLE FOR TABLE PR_HEADER
        insert_header_query = '''
                INSERT INTO pr_header 
                (no_pr, tanggal_permintaan, requester_id, requester_name, nama_project, entity_id, total_budget_approved, remarks, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''

        # EXECUTION QUERY FOR TABLE PR_HEADER
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(insert_header_query, (no_pr, tanggal_permintaan, requester_id, requester_name, nama_project, entity, total_budget_approved, remarks, today, today))
        mysql.connection.commit()

        # INSERT INTO TABLE PR_APPROVAL
        approval_list = []
        idx = 1
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        while True:
            try:
                approval_user_id = request.form[f'approval_user_id{idx}']
                approval_list.append((no_pr, idx, approval_user_id, None, None, today))
                idx += 1
            except KeyError:
                break

        if approval_list:
            insert_approval_query = '''
                INSERT INTO pr_approval (no_pr, approval_no, approval_user_id, status, notes, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            '''
            cursor.executemany(insert_approval_query, approval_list)
            mysql.connection.commit()

        
        # PROVISIONING INSERT INTO TABLE PR_DETAIL
        items = []
        index = 1
        while True:
            try:
                nama_item = request.form[f'nama_item{index}']
                spesifikasi = request.form[f'spesifikasi{index}']
                qty = request.form[f'qty{index}']
                tanggal = request.form[f'tanggal{index}']
                items.append((no_pr, index, nama_item, spesifikasi, qty, tanggal, today, today))
                index += 1
            except KeyError:
                break

        if items:
            insert_detail_query = '''
                INSERT INTO pr_detail (no_pr, item_no, nama_item, spesifikasi, qty, tanggal, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.executemany(insert_detail_query, items)
            mysql.connection.commit()


        # HANDLE FILE UPLOADS
        upload_files = request.files.getlist('files[]')
        upload_docs = []
        for i, file in enumerate(upload_files):
            if file:
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(upload_path)
                relative_path = os.path.relpath(upload_path, 'static')  # UBAH PATHNYA AGAR TIDAK DITULIS STRING static PADA DATABASE
                relative_path = relative_path.replace('\\', '/') # RUBAH BACKSLASH MENJADI SLASH KETIKA INSERT KE DATABASE AGAR DAPAT DI VIEW PADA HTML
                upload_docs.append((no_pr, filename, relative_path, requester_id, today, requester_id, today))

        if upload_docs:
            insert_docs_query = '''
                INSERT INTO pr_docs_reference (no_pr, doc_name, path, created_by, created_at, updated_by, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.executemany(insert_docs_query, upload_docs)
            mysql.connection.commit()
        
        cursor.close()
        flash('New PR has been added', 'success')


        # MULTIPLE SENT MAIL________________________________________________________________
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # query_mail = '''
        # SELECT 
        #     no_pr,
        #     approval_user_id,
        #     ua.username,
        #     ua.email 
        # FROM pr_approval pa 
        # LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
        # WHERE no_pr = %s
        # '''
        # cur.execute(query_mail, [no_pr])
        # data_email = cur.fetchall()
        # cur.close()
        
        # emails = [row['email'] for row in data_email if row['email']]
        # email_list = ', '.join(emails)
        # pr_alert_mail(no_pr, email_list)


        # SINGLE TO FIRST APPROVAL SENT MAIL________________________________________________________________
        query_single_mail = '''
            SELECT 
                no_pr,
                approval_no,
                approval_user_id,
                ua.username,
                ua.email 
            FROM pr_approval pa 
            LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
            WHERE no_pr = %s
            ORDER BY 2 ASC
            LIMIT 1
        '''
        cur.execute(query_single_mail, [no_pr])
        first_approval_mail = cur.fetchone()

        mail_approval_recipient = first_approval_mail['email']
        pr_alert_mail(no_pr, mail_approval_recipient)

        cur.close()

        return redirect(url_for('pr.pr_list'))
    return render_template('pr/pr_temp.html', pr_number=pr_number, entities=entities, departments=departments, approver=approver)
# ==========================================================================================================================================


# PR BACKUP 2024-08-14 
from flask import Blueprint, redirect, render_template, request, session, url_for, flash, jsonify, current_app, send_file
import os
from werkzeug.security import check_password_hash, generate_password_hash
from modules.time import convert_time_to_wib
from datetime import datetime, timedelta, timezone
from modules.decorator import login_required, check_access
from functools import wraps
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepInFrame, Frame
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
from flask_mysqldb import MySQL, MySQLdb
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
from modules.mail import pr_mail, approval_notification_mail, alert_mail, pr_alert_mail
from modules.logs import insert_pr_log
import socket



# ====================================================================================================================================
# PR UTILITES
# ====================================================================================================================================
# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'loggedin' not in session:
#             return redirect(url_for('auth.auth'))
#         return f(*args, **kwargs)
#     return decorated_function

# GET USER IP ADDRESS _________________________________________________________________
device = socket.gethostname()
ip_address = socket.gethostbyname(device)

# INSERT PR_LOGS TABLE  _______________________________________________________________
def insert_pr_log(no_pr, user_id, status, description, ip_address, today):
    from app import mysql
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO pr_logs (no_pr, user_id, status, description, ip_address, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (no_pr, user_id, status, description, ip_address, today)
        )
        mysql.connection.commit()
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        cur.close()
    return "Success insert to log"

def process_and_insert_logs(no_pr, requester_id, ip_address):
    from app import mysql
    cur = mysql.connection.cursor()
    
    log_mail_user = '''
        SELECT 
            no_pr,
            approval_no,
            approval_user_id,
            ua.username,
            ua.email 
        FROM pr_approval pa 
        LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
        WHERE no_pr = %s
        ORDER BY 2 ASC
    '''
    cur.execute(log_mail_user, [no_pr])
    logs_mail = cur.fetchall()

    email_descriptions = []
    sender_email = 'procurement@byorange.co.id'
    for log in logs_mail:
        _, _, _, username, email = log
        email_descriptions.append(f'{username} ({email})')

    if email_descriptions:
        description = f'Sent for signature to {", ".join(email_descriptions)} from {sender_email}'
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Insert the combined log entry into pr_logs
        insert_pr_log(no_pr, requester_id, "SENT", description, ip_address, today)

    cur.close()

# # INSERT PR_LOGS TABLE APPEND____________________________________________________________
# def insert_pr_log_batch(log_entries):
#     from app import mysql
#     try:
#         cur = mysql.connection.cursor()
#         cur.executemany("INSERT INTO pr_logs (no_pr, user_id, status, description, ip_address, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
#                         log_entries)
#         mysql.connection.commit()
#     except Exception as e:
#         print(f'Error: {str(e)}')
#     finally:
#         cur.close()
#     return "Success insert to log"

# def process_and_insert_logs(no_pr, requester_id, ip_address):
#     from app import mysql
#     cur = mysql.connection.cursor()
    
#     log_mail_user = '''
#         SELECT 
#             no_pr,
#             approval_no,
#             approval_user_id,
#             ua.username,
#             ua.email 
#         FROM pr_approval pa 
#         LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
#         WHERE no_pr = %s
#     '''
#     cur.execute(log_mail_user, [no_pr])
#     logs_mail = cur.fetchall()

#     # Prepare data for batch insertion into pr_logs
#     log_entries = []
#     today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
#     for log in logs_mail:
#         no_pr, approval_no, approval_user_id, username, email = log
#         description = f'Approval {approval_no} Sent for signature to({email}), {username}'
#         log_entries.append((no_pr, requester_id, "SENT", description, ip_address, today))
#         print(f'HAAAAAAAAAALOOOOOOOOOOOOOO O O O O O O O O O {log_entries}')

#     # Insert all log entries into pr_logs
#     if log_entries:
#         insert_pr_log_batch(log_entries)

#     cur.close()

# LOCK ADDRESS LOGIN REQUIRED  ____________________________________________________________
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            next_url = request.url
            logging.debug(f"Redirecting to login, next URL: {next_url}")
            return redirect(url_for('auth.login', next=next_url))
        return f(*args, **kwargs)
    return decorated_function


# BLUEPRINT AUTH VARIABLE
pr_blueprint = Blueprint('pr', __name__)
# ====================================================================================================================================


# ====================================================================================================================================
# PR MAIN LIST
# ====================================================================================================================================
@pr_blueprint.route('/pr_list')
@login_required
def pr_list():
    from app import mysql
    import traceback
    
    user_id = session.get('id', 'system')
    if user_id == 'system':
        return redirect(url_for('login'))  # Redirect to login if session is not set

    try:
        cursor = mysql.connection.cursor()
        query = '''
        SELECT DISTINCT 
            ph.no_pr,
            DATE(ph.tanggal_permintaan)tanggal_permintaan,
            ph.requester_id,
            ph.requester_name,
            ph.nama_project,
            ph.entity_id,
            e.entity_name,
            ph.total_budget_approved,
            ph.remarks,
            ph.created_at
        FROM pr_header ph 
        LEFT JOIN pr_detail pd ON ph.no_pr = pd.no_pr 
        LEFT JOIN pr_approval pa ON ph.no_pr = pa.no_pr 
        LEFT JOIN entity e ON ph.entity_id = e.id
        WHERE ph.entity_id IN (
        SELECT DISTINCT entity_id
        FROM user_entity WHERE user_id = %s
        )
        AND (ph.requester_id = %s OR pa.approval_user_id = %s)
        ORDER BY 9 ASC
        '''
        cursor.execute(query, (user_id, user_id, user_id))
        data = cursor.fetchall()

        query_app = "SELECT status FROM pr_approval"
        cursor.execute(query_app)
        appr = cursor.fetchone()
    except Exception as e:
        traceback.print_exc()  # Print stack trace for debugging
        return "An error occurred while fetching the PR list."
    finally:
        cursor.close()
    
    return render_template('pr/pr_list.html', data=data, appr=appr)

# ====================================================================================================================================


# ====================================================================================================================================
# PR FORM SUBMIT
# ====================================================================================================================================
# GET SEQUENCE PR AUTONUMBER
def get_next_sequence(entity, department):
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    from app import mysql

    cursor = mysql.connection.cursor()
    query = '''
        SELECT pr_no FROM pr_autonum
        WHERE entity = %s AND department = %s AND month = %s AND year = %s
        ORDER BY created_at DESC LIMIT 1
    '''
    cursor.execute(query, (entity, department, current_month, current_year))
    last_pr = cursor.fetchone()

    if last_pr:
        last_sequence_number = int(last_pr[0].split('-')[-1])
        next_sequence_number = last_sequence_number + 1
    else:
        next_sequence_number = 1

    cursor.close()
    return next_sequence_number


# EXTRACT AND JOIN PR AUTONUMBER BY DATE
def generate_pr_number(entity, department):
    current_date = datetime.now()
    year_month = current_date.strftime('%y%m')
    sequence_number = f"{get_next_sequence(entity, department):03d}"
    pr_number = f"PR-{entity}-{department}-{year_month}-{sequence_number}"
    return pr_number


# EXTRACT AND JOIN PR AUTONUMBER BY DATE
@pr_blueprint.route('/generate_pr', methods=['GET', 'POST'])
def generate_pr():
    data = request.json
    entity = data['entity']
    department = data['department']
    pr_number = generate_pr_number(entity, department)
    return jsonify({'pr_number': pr_number})


# MAIN PR SUBMIT_________________________________________________________________
@pr_blueprint.route('/pr_temp_submit', methods=['GET', 'POST'])
@login_required
def pr_temp_submit():
    pr_number = None

    # GET ENTITY AND DEPARTMENT
    from app import mysql

    # get user by entities form session
    user_entities = session.get('entities', [])

    # convert entities to list id if user have access more than 1 entity
    entity_ids = [entity['entity_id'] for entity in user_entities]
    cursor = mysql.connection.cursor()

    if entity_ids:
        cursor.execute("SELECT id, entity, entity_name FROM entity WHERE id IN %s", (tuple(entity_ids),))
        entities = cursor.fetchall()
    else:
        entities = []

    # get department list
    cursor.execute("SELECT id, entity_id, department, department_name FROM department WHERE entity_id = 1")
    departments = cursor.fetchall()

    # get approval list
    cursor.execute("SELECT id, username, email FROM user_accounts WHERE level = 4")
    approver = cursor.fetchall()
    
    if request.method == 'POST':
        try:
            # VARIABLE PR HEADER
            entity = request.form['entity']
            department = request.form['department']
            no_pr = generate_pr_number(entity, department)
            tanggal_permintaan = request.form['tanggal_permintaan']
            requester_name = session.get('username', 'system')  # get the username from session auth
            requester_id = session.get('id', 'system')  # get id user from session auth
            total_budget_approved = request.form['total_budget_approved']
            nama_project = request.form['nama_project']
            remarks = None

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

            # ADD CONDITION FOR INSERT TO DB BY entity_id
            if entity == 'CNI':
                entity = 1
            elif entity == 'OID':
                entity = 2
            elif entity == 'RKI':
                entity = 3
            elif entity == 'DMI':
                entity = 4
            elif entity == 'AGI':
                entity = 5
            elif entity == 'OPN':
                entity = 6
            elif entity == 'ATI':
                entity = 7
            elif entity == 'AMP':
                entity = 8
            elif entity == 'TKM':
                entity = 9
            else:
                entity = None

            # INSERT INTO TABLE FOR TABLE PR_HEADER
            insert_header_query = '''
                    INSERT INTO pr_header 
                    (no_pr, tanggal_permintaan, requester_id, requester_name, nama_project, entity_id, total_budget_approved, remarks, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''

            # EXECUTION QUERY FOR TABLE PR_HEADER
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(insert_header_query, (no_pr, tanggal_permintaan, requester_id, requester_name, nama_project, entity, total_budget_approved, remarks, today, today))
            mysql.connection.commit()

            # INSERT INTO TABLE PR_APPROVAL
            approval_list = []
            idx = 1
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            while True:
                try:
                    approval_user_id = request.form[f'approval_user_id{idx}']
                    approval_list.append((no_pr, idx, approval_user_id, None, None, today))
                    idx += 1
                except KeyError:
                    break

            if approval_list:
                insert_approval_query = '''
                    INSERT INTO pr_approval (no_pr, approval_no, approval_user_id, status, notes, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                '''
                cursor.executemany(insert_approval_query, approval_list)
                mysql.connection.commit()

            
            # PROVISIONING INSERT INTO TABLE PR_DETAIL
            items = []
            index = 1
            while True:
                try:
                    nama_item = request.form[f'nama_item{index}']
                    spesifikasi = request.form[f'spesifikasi{index}']
                    qty = request.form[f'qty{index}']
                    tanggal = request.form[f'tanggal{index}']
                    items.append((no_pr, index, nama_item, spesifikasi, qty, tanggal, today, today))
                    index += 1
                except KeyError:
                    break

            if items:
                insert_detail_query = '''
                    INSERT INTO pr_detail (no_pr, item_no, nama_item, spesifikasi, qty, tanggal, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                '''
                cursor.executemany(insert_detail_query, items)
                mysql.connection.commit()


            # HANDLE FILE UPLOADS
            upload_files = request.files.getlist('files[]')
            upload_docs = []
            for i, file in enumerate(upload_files):
                if file:
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(upload_path)
                    relative_path = os.path.relpath(upload_path, 'static')  # UBAH PATHNYA AGAR TIDAK DITULIS STRING static PADA DATABASE
                    relative_path = relative_path.replace('\\', '/') # RUBAH BACKSLASH MENJADI SLASH KETIKA INSERT KE DATABASE AGAR DAPAT DI VIEW PADA HTML
                    upload_docs.append((no_pr, filename, relative_path, requester_id, today, requester_id, today))

            if upload_docs:
                insert_docs_query = '''
                    INSERT INTO pr_docs_reference (no_pr, doc_name, path, created_by, created_at, updated_by, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                '''
                cursor.executemany(insert_docs_query, upload_docs)
                mysql.connection.commit()
            
            flash('New PR has been added', 'success')
            
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            query_single_mail = '''
                SELECT 
                    no_pr,
                    approval_no,
                    approval_user_id,
                    ua.username,
                    ua.email 
                FROM pr_approval pa 
                LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
                WHERE no_pr = %s
                ORDER BY 2 ASC
                LIMIT 1
            '''
            cur.execute(query_single_mail, [no_pr])
            first_approval_mail = cur.fetchone()
            cur.close()

            mail_approval_recipient = first_approval_mail['email']
            pr_alert_mail(no_pr, mail_approval_recipient)
            process_and_insert_logs(no_pr, requester_id, ip_address)
            return redirect(url_for('pr.pr_list'))
        
        except Exception as e:
            # ROLLBACK QUERY IF THERE IS AN ERROR OCCURE
            mysql.connection.rollback()
            flash(f'Error: {str(e)}', 'warning')
            return redirect(url_for('pr.pr_temp_submit'))


        # MULTIPLE SENT MAIL________________________________________________________________
        # cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # query_mail = '''
        # SELECT 
        #     no_pr,
        #     approval_user_id,
        #     ua.username,
        #     ua.email 
        # FROM pr_approval pa 
        # LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
        # WHERE no_pr = %s
        # '''
        # cur.execute(query_mail, [no_pr])
        # data_email = cur.fetchall()
        # cur.close()
        
        # emails = [row['email'] for row in data_email if row['email']]
        # email_list = ', '.join(emails)
        # pr_alert_mail(no_pr, email_list)


        # SINGLE TO FIRST APPROVAL SENT MAIL________________________________________________________________


    # return redirect(url_for('pr.pr_list'))
    return render_template('pr/pr_temp.html', pr_number=pr_number, entities=entities, departments=departments, approver=approver)
# ==========================================================================================================================================


# @pr_blueprint.route('/pr_detail_page', methods=['GET', 'POST'])
# def pr_detail_page():
#     return render_template('pr/pr_detail.html')

import logging

# Set up logging
# logging.basicConfig(level=logging.DEBUG)



# ====================================================================================================================================
# PT DETAIL
# ====================================================================================================================================
@pr_blueprint.route('/pr_detail_page/<no_pr>', methods=['GET', 'POST'])
@login_required
def pr_detail_page(no_pr):
    from app import mysql
    cur = mysql.connection.cursor()

    # GET USER_ID FROM LOGIN SESSION
    current_user_id = session.get('id', 'system')

    # QUERY LIST FOR PR_HEADER DATA___________________________________________________
    query = """
            SELECT DISTINCT 
                ph.no_pr,
                DATE(ph.tanggal_permintaan)tanggal_permintaan,
                ph.requester_id,
                ph.requester_name,
                ph.entity_id,
                ph.nama_project,
                ph.total_budget_approved,
                ph.remarks,
                e.entity,
                e.entity_name
            FROM pr_header ph 
            LEFT JOIN entity e ON ph.entity_id = e.id
            WHERE ph.no_pr = %s
    """
    cur.execute(query, [no_pr])
    pr_header = cur.fetchall()
    
    # Log data for debugging
    logging.debug(f"Data fetched for no_pr {no_pr}: {pr_header}")

    # QUERY LIST FOR PR_DETAIL__________________________________________________________
    cur.execute("SELECT no_pr, item_no, nama_item, spesifikasi, qty, tanggal FROM pr_detail WHERE no_pr = %s", (no_pr,))
    pr_detail = cur.fetchall()

    # QUERY LIST FOR APPROVAL___________________________________________________________
    query_approval = """
            SELECT 
                pa.no_pr,
                pa.approval_user_id,
                ua.username,
                pa.status,
                pa.notes,
                pa.approval_no,
                pa.created_at
            FROM pr_approval pa
            LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id
            WHERE no_pr = %s
    """
    cur.execute(query_approval, [no_pr])
    pr_approval = cur.fetchall()

    # QUERY LIST FOR PR_DOCS_UPLOAD__________________________________________________________
    cur.execute("SELECT DISTINCT no_pr, doc_name, path FROM pr_docs_reference WHERE no_pr = %s", (no_pr,))
    pr_docs = cur.fetchall()

    cur.close()

    return render_template('pr/pr_detail.html', pr_header=pr_header, pr_detail=pr_detail, pr_approval=pr_approval, pr_docs=pr_docs, current_user_id=current_user_id)
# ====================================================================================================================================

# ====================================================================================================================================
# PT DETAIL MANUAL SEND MAIL
# ====================================================================================================================================
@pr_blueprint.route('/pr_send_mail_manual/<approval_id>/<no_pr>', methods=['GET', 'POST'])
@login_required
def pr_send_mail_manual(approval_id, no_pr):
    from app import mysql
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = """
        SELECT DISTINCT 
            ph.no_pr,
            DATE(ph.tanggal_permintaan) AS tanggal_permintaan,
            ph.requester_id,
            ph.requester_name,
            ph.entity_id,
            ph.nama_project,
            ph.total_budget_approved,
            ph.remarks,
            e.entity,
            e.entity_name,
            pa.approval_user_id,
            ua.email,
            ua.username,
            pd.tanggal,
            SUM(pd.qty)qty
        FROM pr_header ph 
        LEFT JOIN entity e ON ph.entity_id = e.id
        LEFT JOIN pr_detail pd ON ph.no_pr = pd.no_pr 
        LEFT JOIN pr_approval pa ON ph.no_pr = pa.no_pr 
        LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id
        WHERE ph.no_pr = %s
        AND pa.approval_user_id = %s
        GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14
    """
    cur.execute(query, [no_pr, approval_id])
    data_email = cur.fetchone()

    
    today = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
    nama_project = data_email['nama_project']
    nama_entity = data_email['entity_name']
    nama_requester = data_email['requester_name']
    budget = data_email['total_budget_approved']
    tanggal_request = data_email['tanggal_permintaan']
    mail_recipient = data_email['email']
    due_date = data_email['tanggal']
    approval_name = data_email['username']

    try:
        alert_mail(no_pr, mail_recipient, nama_project, nama_entity, nama_requester, tanggal_request, budget, due_date, approval_name, today)
        flash(f'Mail has been sent to {mail_recipient}', 'success')

    except Exception as e:
        print(f"Error :{e}")
        flash(f'Email not sent {e}', 'warning')

    return redirect(url_for('pr.pr_list')) 
    # return f"test kirim ke email: {due_date} approval_name: {approval_name} approval_mail: {mail_recipient}"


# ====================================================================================================================================
# PR APPROVED & REJECTED
# ====================================================================================================================================

# MAIL APPROVAL ______________________________________________________________________________________________________________________
def send_sequence_mail_pr(no_pr):

    from app import mysql
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor) #PAKE DICT 

    query = '''
        SELECT DISTINCT
            ph.no_pr,
            pa.approval_no,
            pa.approval_user_id,
            ua.email,
            pa.status 
        FROM pr_header ph 
        LEFT JOIN pr_approval pa ON ph.no_pr = pa.no_pr
        LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
        WHERE pa.status IS NULL
        AND ph.no_pr = %s
        ORDER BY approval_no DESC
        LIMIT 1
    '''
    cur.execute(query, [no_pr])
    data = cur.fetchone()
    email = data['email']
    cur.close()

    return email

# APPROVED ____________________________________________________________________________________________________________________________
@login_required
@pr_blueprint.route('/pr_approved/<no_pr>', methods=['GET', 'POST'])
def pr_approved(no_pr):
    from app import mysql
    cur = mysql.connection.cursor()
    current_user_id = session.get('id', 'system')


    if request.method == 'POST':
        approval_notes = request.form.get('notes')
        approval_user_id = current_user_id

        # Update query
        update_query = f"""
            UPDATE pr_approval
            SET status = 'APPROVED', notes = %s, created_at = NOW()
            WHERE no_pr = %s AND approval_user_id = %s
        """

        print(approval_user_id)

        try:
            cur.execute(update_query, (approval_notes, no_pr, approval_user_id))
            mysql.connection.commit()
            mail_next_approval = send_sequence_mail_pr(no_pr)
            pr_alert_mail(no_pr, mail_next_approval)

            flash('PR has been APPROVED successfully!', 'success')

        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error: {str(e)}', 'danger')
        finally:
            cur.close()
    
    return redirect(url_for('pr.pr_list')) 


# REJECTED ___________________________________________________________________________________________________________________________
@pr_blueprint.route('/pr_rejected/<no_pr>', methods=['GET', 'POST'])
@login_required
def pr_rejected(no_pr):
    from app import mysql
    cur = mysql.connection.cursor()
    current_user_id = session.get('id', 'system')


    if request.method == 'POST':
        approval_notes = request.form.get('notes')
        approval_user_id = current_user_id

        # Update query
        update_query = f"""
            UPDATE pr_approval
            SET status = 'REJECTED', notes = %s, created_at = NOW()
            WHERE no_pr = %s AND approval_user_id = %s
        """

        try:
            cur.execute(update_query, (approval_notes, no_pr, approval_user_id))
            mysql.connection.commit()
            email = 'rohmankpai@gmail.com'
            requestName = 'Mohammad Nurohman'
            approvalName = 'David Irwan'
            entityName = 'PT. ORANGE INOVASI DIGITAL'
            budget = "2000000"
            dueDate = '2024-08-01'
            # pr_mail(no_pr, email, requestName, approvalName, budget, dueDate, entityName)
            flash('PR has been REJECTED successfully!', 'success')

        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error: {str(e)}', 'danger')
        finally:
            cur.close()
    
    return redirect(url_for('pr.pr_list')) 

# ====================================================================================================================================



# ====================================================================================================================================
# PR UDPATE
# ====================================================================================================================================
@pr_blueprint.route('/pr_edit/<no_pr>', methods=['GET', 'POST'])
@login_required
def pr_edit(no_pr):
    from app import mysql

    cur = mysql.connection.cursor()
    user_id = session.get('id', 'system')

    # GET PR_HEADER
    cur.execute('''
        SELECT DISTINCT 
            ph.no_pr,
            DATE(ph.tanggal_permintaan)tanggal_permintaan,
            ph.requester_id,
            ph.requester_name,
            ph.entity_id,
            ph.nama_project,
            ph.total_budget_approved,
            ph.remarks,
            e.entity,
            e.entity_name
        FROM pr_header ph 
        LEFT JOIN entity e ON ph.entity_id = e.id
        WHERE ph.no_pr = %s''', (no_pr, ))

    pr_header = cur.fetchone()

    # GET PR_DETAIL
    cur.execute('''
        SELECT
            no_pr,
            item_no,
            nama_item,
            spesifikasi,
            qty,
            tanggal
        FROM pr_detail
        WHERE no_pr = %s''', (no_pr, ))

    pr_detail = cur.fetchall()

    # GET PR_APPROVAL
    cur.execute("SELECT id, username, email FROM user_accounts WHERE level = 4")
    approver = cur.fetchall()

    cur.execute('''
        SELECT 
            pa.no_pr,
            pa.approval_no,
            pa.approval_user_id,
            ua.username,
            pa.status,
            pa.notes
        FROM pr_approval pa
        LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id
        WHERE no_pr = %s
    ''', (no_pr, ))

    pr_approval = cur.fetchall()

    # GET PR_DOCUMENTS
    cur.execute('''
        SELECT 
            id,
            no_pr,
            doc_name,
            `path`
        FROM pr_docs_reference
        WHERE no_pr = %s
    ''', (no_pr, ))

    pr_documents = cur.fetchall()

    if pr_header is None or pr_detail is None or pr_approval is None:
        flash('PR Not Found', 'danger')
        return redirect(url_for('pr.pr_list'))

    if request.method == 'POST':

        # FOR UPDATE PR_HEADER VALUES________________________________________________________________________________
        nama_project = request.form['nama_project']
        total_budget = request.form['total_budget_approved']
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            cur.execute('''
                UPDATE pr_header 
                SET nama_project=%s, total_budget_approved=%s, updated_at=%s 
                WHERE no_pr = %s
            ''', (nama_project, total_budget, today, no_pr))
        except Exception as e:
            print(e)

        mysql.connection.commit()
    
        # FOR UPDATE DETAIL__________________________________________________________________________________________
        # GETTING LIST DETAIL
        cur.execute("SELECT item_no, nama_item, spesifikasi, qty, tanggal FROM pr_detail WHERE no_pr = %s", (no_pr,))
        existing_details = cur.fetchall()

        # CONVERT LIST DETAIL QUERY YANG SUDAH ADA DI TABLE TO DICT AGAR MUDAH UNTUK COMPARE ID YANG AKAN DIEKSEKUSI
        existing_details_dict = {item[0]: item for item in existing_details}

        # DAPATKAN VALUE BARU DARI FORM HTML UNTUK DI INSERT, UPDATE ATAU DELETE
        new_details = []
        index = 1
        # deleted_id = []
        while True:
            try:
                nama_item = request.form[f'nama_item{index}']
                spesifikasi = request.form[f'spesifikasi{index}']
                qty = request.form[f'qty{index}']
                tanggal = request.form[f'tanggal{index}']
                new_details.append((index, nama_item, spesifikasi, qty, tanggal))
                index += 1
            except KeyError:
                break

        # CONVERT ID YANG BARU SAJA DI INPUT DALAM HTML UNTUK DIKOMPARASI DENGAN ID YANG LAMA
        new_details_dict = {item[0]: item for item in new_details}

        # IDENTIFIKASI DETAIL YANG ININ DI INSERT, UDPATE ATAU DELETE
        details_to_insert = []
        details_to_update = []
        details_to_delete = []
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # BUAT LOOPING DARI INDEX (ITEM NUMBER) HTML DAN KONDISI
        # KONDISINYA JIKA TIDAK ADA INDEX BARU PADA INPUTAN MAKA STATUSNYA DI INSERT BARU
        # JIKA STATUSNYA INDEX TERSEBUT ADA TAPI ADA PERUBAHAN MAKA AKAN DIUPDATE DATANYA
        # JIKA STATUSNYA INDEX TERSEBUT DIKOMPARE ANTARA INDEX LAMA DENGAN INDEX BARU DAN TERNYATA TIDAK ADA PADA INDEX BARU MAKA DATA TERSEBUT AKAN DIHAPUS
        for index, detail in new_details_dict.items():
            if index not in existing_details_dict:
                details_to_insert.append((no_pr, index, detail[1], detail[2], detail[3], detail[4], today, today))
            elif detail != existing_details_dict[index]:
                details_to_update.append((detail[1], detail[2], detail[3], detail[4], today, no_pr, index))

        for index in existing_details_dict:
            if index not in new_details_dict:
                details_to_delete.append(index)

        # INSERT NEW DATA
        if details_to_insert:
            insert_query = '''
                INSERT INTO pr_detail (no_pr, item_no, nama_item, spesifikasi, qty, tanggal, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            cur.executemany(insert_query, details_to_insert)

        # UDPATE EXISTING DATA
        if details_to_update:
            update_query = '''
                UPDATE pr_detail
                SET nama_item = %s, spesifikasi = %s, qty = %s, tanggal = %s, updated_at = %s
                WHERE no_pr = %s AND item_no = %s
            '''
            cur.executemany(update_query, details_to_update)

        # DELETE OLD DATA WHEN NOT USED
        if details_to_delete:
            delete_query = '''
                DELETE FROM pr_detail
                WHERE no_pr = %s AND item_no = %s
            '''
            cur.executemany(delete_query, [(no_pr, index) for index in details_to_delete])

        mysql.connection.commit()


        # INSERT NEW APPROVAL________________________________________________________________________________________
        # GETTING LIST APPROVAL
        cur.execute("SELECT approval_no, approval_user_id, status, notes FROM pr_approval WHERE no_pr = %s", (no_pr,))
        existing_approval = cur.fetchall()
        existing_approval_dict = {item[0]: item for item in existing_approval}
        
        new_approval = []
        idx = 1
        while True:
            try:
                approval_user_id = request.form[f'approval{idx}_user_id']
                new_approval.append((idx, approval_user_id))
                idx += 1
            except KeyError:
                break
        
        new_approval_dict = {item[0]: item for item in new_approval}

        approval_to_insert = []
        approval_to_update = []
        approval_to_delete = []

        for idx, value in new_approval_dict.items():
            if idx not in existing_approval_dict:
                approval_to_insert.append((no_pr, idx, value[1], None, None, today))
            elif value != existing_approval_dict[idx]:
                approval_to_update.append((value[1], None, None, today, no_pr, idx))

        for idx in existing_approval_dict:
            if idx not in new_approval_dict:
                approval_to_delete.append(idx)

        if approval_to_insert:
            insert_query = '''
                INSERT INTO pr_approval (no_pr, approval_no, approval_user_id, status, notes, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            '''
            cur.executemany(insert_query, approval_to_insert)

        if approval_to_update:
            update_query = '''
                UPDATE pr_approval
                SET approval_user_id = %s, status = %s, notes = %s, created_at = %s
                WHERE no_pr = %s AND approval_no = %s
            '''
            cur.executemany(update_query, approval_to_update)

        if approval_to_delete:
            delete_query = '''
                DELETE FROM pr_approval
                WHERE no_pr = %s AND approval_no = %s
            '''
            cur.executemany(delete_query, [(no_pr, index) for index in approval_to_delete])

        mysql.connection.commit()
                
        # INSERT NEW UPLOADS________________________________________________________________________________________
        upload_files = request.files.getlist('files[]')
        upload_docs = []
        for i, file in enumerate(upload_files):
            if file:
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(upload_path)
                relative_path = os.path.relpath(upload_path, 'static')  # UBAH PATHNYA AGAR TIDAK DITULIS STRING static PADA DATABASE
                relative_path = relative_path.replace('\\', '/') # RUBAH BACKSLASH MENJADI SLASH KETIKA INSERT KE DATABASE AGAR DAPAT DI VIEW PADA HTML
                upload_docs.append((no_pr, filename, relative_path, user_id, today, user_id, today))

        if upload_docs:
            insert_docs_query = '''
                INSERT INTO pr_docs_reference (no_pr, doc_name, path, created_by, created_at, updated_by, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cur.executemany(insert_docs_query, upload_docs)
            mysql.connection.commit()
            
        # UPDATE UPLOAD FILES
        existing_files = request.files # LIST ATAU GET FILE YANG DIUPLOAD SEBELUMNYA DAPAT VALUENYA BALIKAN DARI DATABASE YANG ADA DI HTML
        for file_id, file in existing_files.items():
            if file and 'existing_files[' in file_id: # CHEKC FILE YANG AKAN DIUNGGAH APAKAH EXISITNG ATAU TIDAK PENANDANYA MENGGUNAKAN 'existing_files['
                
                # Dari file_id seperti existing_files[1], kita mengekstrak ID file. lalu pisahin dengan split('[') buat memisahkan string menjadi daftar berdasarkan [, 
                # kemudian [-1][:-1] mengambil bagian terakhir dari daftar (yaitu 1]) dan menghapus karakter ] dari akhirnya, sehingga kita mendapatkan 1.
                actual_file_id = file_id.split('[')[-1][:-1]
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(upload_path)
                relative_path = os.path.relpath(upload_path, 'static') 
                relative_path = relative_path.replace('\\', '/')
                update_docs_query = '''
                    UPDATE pr_docs_reference
                    SET doc_name = %s, path = %s, updated_by = %s, updated_at = %s
                    WHERE id = %s
                '''
                cur.execute(update_docs_query, (filename, relative_path, user_id, today, actual_file_id))
                mysql.connection.commit()

        # DELETE UPLOADS FILE FROM DB
        deleted_files = request.form.getlist('deleted_files[]')
        if deleted_files:
            delete_docs_query = '''
                DELETE FROM pr_docs_reference WHERE id IN (%s)
            ''' % ', '.join(['%s'] * len(deleted_files))
            cur.execute(delete_docs_query, tuple(deleted_files))
            mysql.connection.commit()

        cur.close()
        flash('PR updated successfully', 'success')
        return redirect(url_for('pr.pr_list'))

    # return render_template('pr/pr_edit.html', pr_header=pr_header, pr_details=pr_details, pr_approvals=pr_approvals, entities=entities, departments=departments, approver=approver)
    return render_template('pr/pr_edit.html', pr_header=pr_header, pr_detail=pr_detail, pr_approval=pr_approval, pr_documents=pr_documents, approver=approver)
# ====================================================================================================================================


# ====================================================================================================================================
# GENERATE PR TO PDF
# ====================================================================================================================================
@pr_blueprint.route('/pr_generate_pdf/<no_pr>', methods=['GET', 'POST'])
@login_required
def pr_generate_pdf(no_pr):
    from app import mysql

    cur = mysql.connection.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    requester_id = session.get('id', 'system')
    # DEFINE ALL TABLE RELATE TO PR
    # GET PR_HEADER
    cur.execute('''
        SELECT DISTINCT 
            ph.no_pr,
            DATE(ph.tanggal_permintaan)tanggal_permintaan,
            ph.requester_id,
            ph.requester_name,
            ph.entity_id,
            ph.nama_project,
            ph.total_budget_approved,
            ph.remarks,
            e.entity,
            ua.sign_path 
        FROM pr_header ph 
        LEFT JOIN entity e ON ph.entity_id = e.id
        LEFT JOIN user_accounts ua ON ph.requester_id = ua.id
        WHERE ph.no_pr = %s''', (no_pr, ))

    pr_header = cur.fetchone()

    # GET PR_DETAIL
    cur.execute('''
        SELECT
            no_pr,
            item_no,
            nama_item,
            spesifikasi,
            qty,
            tanggal
        FROM pr_detail
        WHERE no_pr = %s''', (no_pr, ))

    pr_details = cur.fetchall()

    # GET PR_APPROVAL
    cur.execute("SELECT sign_path FROM user_accounts WHERE id = %s",(requester_id,))
    reqester_ttd = cur.fetchall()

    cur.execute('''
        SELECT 
            pa.no_pr,
            pa.approval_no,
            pa.approval_user_id,
            ua.username,
            pa.status,
            pa.notes,
            CASE 
                WHEN pa.status = 'APPROVED' THEN DATE(pa.created_at)
                WHEN pa.status = 'REJECTED' THEN DATE(pa.created_at)
                ELSE 'PENDING'
            END approval_date,
            CASE 
                WHEN pa.status = 'APPROVED' THEN ua.sign_path
                ELSE NULL
            END sign_path
        FROM pr_approval pa
        LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id
        WHERE no_pr = %s
    ''', (no_pr, ))

    pr_approval = cur.fetchall()

    # GET PR_DOCUMENTS
    cur.execute('''
        SELECT 
            no_pr,
            doc_name,
            `path`
        FROM pr_docs_reference
        WHERE no_pr = %s
    ''', (no_pr, ))

    pr_documents = cur.fetchall()

    # MAIN FORM PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # PARSE DATE
    created_at = pr_header[1] if pr_header[1] else None
    if isinstance(created_at, str):
        created_at = datetime.datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')

    # CUSTOM STYLE
    centered_style = ParagraphStyle(name='centered', alignment=TA_CENTER, fontSize=10, fontName='Helvetica')
    lefted_style = ParagraphStyle(name='lefted', alignment=TA_LEFT, fontSize=10, fontName='Helvetica')
    title_style = ParagraphStyle(name='title', alignment=TA_CENTER, fontSize=20, fontName='Helvetica-Bold')
    table_content_style = ParagraphStyle(name='table_content', alignment=TA_CENTER, fontSize=10)
    table_content_style_left = ParagraphStyle(name='table_content_left', alignment=TA_LEFT, fontSize=10)
    table_header_style = ParagraphStyle(name='table_header', alignment=TA_CENTER, fontSize=10, fontName='Helvetica-Bold')
    footer_style = ParagraphStyle(name='footer', fontSize=10, fontName='Helvetica-Bold')
    name_footer_style = ParagraphStyle(name='footer', fontSize=10, fontName='Helvetica-Bold',  alignment=TA_CENTER)
    detail_key_style = ParagraphStyle(name='detail_key', fontSize=10, fontName='Helvetica-Bold')
    detail_value_style = ParagraphStyle(name='detail_value', fontSize=10)
    date_approval = ParagraphStyle(name='footer', fontSize=8, fontName='Helvetica', alignment=TA_CENTER)

    # FOR TITLE
    title = Paragraph('Purchase Requisition (PR)', title_style)
    elements.append(title)
    elements.append(Spacer(1, 15))

    # PR NUMBER
    pr_number = Paragraph(f'(Form Permintaan Barang / Jasa)', centered_style)
    elements.append(pr_number)
    elements.append(Spacer(1, 11))
    pr_number = Paragraph(f'No. PR: {pr_header[0]}', centered_style)
    elements.append(pr_number)
    elements.append(Spacer(1, 11))

    # PR HEADER DATA
    detail_data = [
        [Paragraph('', detail_key_style), Paragraph('', footer_style)],
        [Paragraph('Tanggal Permintaan', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{created_at.strftime("%d %B %Y") if created_at else "N/A"}', detail_value_style)],
        [Paragraph('User / Requester', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{pr_header[3]}', detail_value_style)],
        [Paragraph('Nama Project', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{pr_header[5]}', detail_value_style)],
        [Paragraph('Sumber Budget / Entity', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{pr_header[8]}', detail_value_style)],
        [Paragraph('Total Budget Approved', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'Rp. {pr_header[6]:,.2f} (PPN Exclude)', detail_value_style)],
        [Paragraph('', detail_key_style), Paragraph('', footer_style)]
    ]

    # PR HEADER TABLE LIST OUTPUT
    table_detail = Table(detail_data, colWidths=[3.9*inch, 0.2*inch, 2.8*inch])
    table_detail.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    elements.append(table_detail)
    elements.append(Spacer(1, 12))

    # PR DETAIL DATA
    # item_description = Paragraph(details[3], ParagraphStyle(name='item_description', alignment=TA_LEFT, fontSize=11, wordWrap='CJK'))
    table_header_style = ParagraphStyle(name='table_header', alignment=1, fontSize=10, fontName='Helvetica-Bold')
    table_content_style = ParagraphStyle(name='table_content', alignment=1, fontSize=10)
    item_description_style = ParagraphStyle(name='item_description', alignment=0, fontSize=10, wordWrap='CJK')

    # PR DETAIL DATA
    table_data = [[ 
          Paragraph('No', table_header_style), 
          Paragraph('Nama Barang/Jasa', table_header_style), 
          Paragraph('Spesifikasi Barang/Jasa', table_header_style), Paragraph('QTY', table_header_style), 
          Paragraph('Tanggal dibutuhkan', table_header_style) ]]

    for details in pr_details:
        due_date = details[5] if details[5] else None
        if isinstance(due_date, str):
            due_date = datetime.datetime.strptime(due_date, '%Y-%m-%d')

        item_description = Paragraph(details[3], item_description_style)

        table_data.append([
            Paragraph(str(details[1]), table_content_style),
            Paragraph(details[2], table_content_style),
            item_description,
            Paragraph(str(details[4]), table_content_style),
            Paragraph(due_date.strftime('%d %b %Y') if due_date else 'N/A', table_content_style)
        ])

    # PR HEADER TABLE LIST DATA OUTPUT
    table = Table(table_data, colWidths=[0.5*inch, 1.5*inch, 3*inch, 0.6*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lemonchiffon),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align content to the top
    ]))
    elements.append(table)
    elements.append(Spacer(1, 1))

    remarks_head = [
        [Paragraph('', detail_key_style), Paragraph('', footer_style)],
        [Paragraph('Remarks:', detail_key_style)],
        [Paragraph('', detail_key_style), Paragraph('', footer_style)]
    ]

    # PR TABLE REMARKS
    remarks_table = Table(remarks_head, colWidths=[5*inch, 1.8*inch])
    remarks_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    elements.append(remarks_table)
    elements.append(Spacer(1, 1))

    # REMKARS FILES  
    lampiran = Paragraph(f'1. Lampirkan gambar jika ada', lefted_style)
    urgent = Paragraph(f'2. Urgent / penunjukan vendor langsung harus melampirkan Form Waiver', lefted_style)
    elements.append(lampiran)
    elements.append(Spacer(1, 12))
    elements.append(urgent)
    elements.append(Spacer(1, 30))

    # PR APPROVAL
    
    styles = getSampleStyleSheet()
    # footer_style = styles['Normal']
    footer_style.alignment = 1  # Center alignment

    # GET REQUESTER APPROVAL NULL OR EXIST SIGN
    requester_sign = pr_header[9] if pr_header[9] else 'static/uploads/white.png'
    signature_image = Image(requester_sign, width=50, height=50)

    # PR APPROVAL SIGNATURE STRUCTURE
    table_footer_data = [
        [Paragraph('Dibuat Oleh', footer_style), Paragraph('Disetujui Oleh', footer_style)]
    ]

    # SPACING BETWEEN NAME AND SIGNATURE
    for x in range(0):
        table_footer_data.append([Paragraph('', footer_style), Paragraph('', footer_style), Paragraph('', footer_style)])

    # ADD REQUESTER SIGNATURE AND NAME
    signature_row = [signature_image]
    date_row = [Paragraph('', date_approval)]
    approval_row = [Paragraph(f'({pr_header[3]})', footer_style)]

    # ADD APPROVAL SIGNATURE DATE APPROVED AND NAMES
    for approval in pr_approval:
        approval_date = str(approval[6]) if str(approval[6]) else ''
        approval_name = f'({approval[3]})' if approval[3] else ''
        sign_path = approval[7] if approval[7] else 'static/uploads/white.png'

        # SIGNATURE DATA
        signature_row.append(Image(sign_path, width=50, height=50))
        # DATE APPROVED
        date_row.append(Paragraph(approval_date, date_approval))
        # APRROVAL NAME DATA
        approval_row.append(Paragraph(approval_name, footer_style))

    # ADD 3 ROWS OR MORE
    while len(approval_row) < 3:
        approval_row.append(Paragraph('', footer_style))
        date_row.append(Paragraph('', date_approval))
        signature_row.append(Paragraph('', footer_style))

    table_footer_data.append(signature_row)
    table_footer_data.append(date_row)
    table_footer_data.append(approval_row)

    table_footer = Table(table_footer_data, colWidths=[2.1 * inch, 2.0 * inch, 2.0 * inch])
    table_footer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))

    elements.append(table_footer)
    elements.append(Spacer(1, 12))

    doc.build(elements)
    doc.setTitle = "PR"

    buffer.seek(0)

    # COMBINE PDF FILES REFERENCES__________________________________________________________
    main_pdf = PdfReader(buffer)
    pdf_writer = PdfWriter()

    # LIST PATH LOCATION
    cur.execute('''
        SELECT path
        FROM pr_docs_reference pdr 
        WHERE no_pr = %s
    ''', (no_pr, ))

    additional_paths = [os.path.join('static', row[0]) for row in cur.fetchall()]

    cur.close()

    # ADD ALL PAGES FROM MAIN PDF
    for page_num in range(len(main_pdf.pages)):
        pdf_writer.add_page(main_pdf.pages[page_num])

    # CONVERT (JPG, JPEG, PNG) IMG FILES
    def convert_image_to_pdf(image_path):
        try:
            img_buffer = BytesIO()
            img_doc = SimpleDocTemplate(img_buffer, pagesize=A4)
            elements = []

            # CREATE IMG OBJECT
            img = Image(image_path)
            img_width, img_height = img.wrap(0, 0)

            # SCALE IMG TO A4 PAPER
            scale = min(A4[0] / img_width, A4[1] / img_height)
            img.drawWidth = img_width * scale
            img.drawHeight = img_height * scale

            # ADD SLACE IMG TO ELEMENT LIST
            elements.append(img)
            
            img_doc.build(elements)
            img_buffer.seek(0)
            print(f"Converted image {image_path} to PDF successfully.")
            return img_buffer
        except Exception as e:
            print(f"Error converting image to PDF: {e}")
            return None

    # Add all pages from the additional files
    for path in additional_paths:
        print(f"Processing file: {path}")
        if path.endswith('.pdf'):
            try:
                with open(path, "rb") as f:
                    additional_pdf = PdfReader(f)
                    for page_num in range(len(additional_pdf.pages)):
                        pdf_writer.add_page(additional_pdf.pages[page_num])
                print(f"Added pages from PDF file: {path}")
            except Exception as e:
                print(f"Error adding PDF file {path}: {e}")
        elif path.endswith('.jpg') or path.endswith('.jpeg') or path.endswith('.png'):
            image_pdf_buffer = convert_image_to_pdf(path)
            if image_pdf_buffer:
                image_pdf = PdfReader(image_pdf_buffer)
                for page_num in range(len(image_pdf.pages)):
                    pdf_writer.add_page(image_pdf.pages[page_num])
                print(f"Added pages from image file: {path}")
            else:
                print(f"Skipping invalid image file: {path}")

    # Write the combined PDF to a new buffer
    combined_buffer = BytesIO()
    pdf_writer.write(combined_buffer)
    combined_buffer.seek(0)

    print("Combined PDF generated successfully.")

    # return send_file(buffer, as_attachment=False, download_name=f'{no_pr}_{today}.pdf', mimetype='application/pdf')
    return send_file(combined_buffer, as_attachment=False, download_name=f'{no_pr}_{today}.pdf', mimetype='application/pdf')
# ========================================================================================================================================


# SEARCH PR BY DATE ======================================================================================================================
@pr_blueprint.route('/pr_search_date', methods=['GET', 'POST'])
def pr_search_date():
    from app import mysql
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        dateRange = request.form['created_at']
        start_date, end_date = dateRange.split(' - ')
        start_date = start_date.replace("/","-")
        start_date = datetime.strptime(start_date, "%m-%d-%Y").strftime("%Y-%m-%d")
        end_date = end_date.replace("/","-")
        end_date = datetime.strptime(end_date, "%m-%d-%Y").strftime("%Y-%m-%d")
        user_id = session.get('id', 'system')

        try:
            query = '''
                SELECT DISTINCT 
                    ph.no_pr,
                    DATE(ph.tanggal_permintaan) AS tanggal_permintaan,
                    ph.requester_id,
                    ph.requester_name,
                    ph.nama_project,
                    ph.entity_id,
                    e.entity_name,
                    ph.total_budget_approved,
                    ph.remarks,
                    ph.created_at
                FROM pr_header ph 
                LEFT JOIN pr_detail pd ON ph.no_pr = pd.no_pr 
                LEFT JOIN pr_approval pa ON ph.no_pr = pa.no_pr 
                LEFT JOIN entity e ON ph.entity_id = e.id
                WHERE ph.entity_id IN (
                SELECT DISTINCT entity_id
                FROM user_entity WHERE user_id = %s
                )
                AND (ph.requester_id = %s OR pa.approval_user_id = %s)
                AND DATE(ph.created_at) BETWEEN %s AND %s
            '''
            cur.execute(query, (user_id, user_id, user_id, start_date, end_date))
            data = cur.fetchall()
            cur.close()
        
        except Exception as e:
            print(f"ERROR cannot be fetched: {e}")

        return render_template('pr/pr_list.html', data=data)
        # return f"start_date: {start_date}, end_date: {end_date}, user_id: {user_id}"

    return render_template('pr/search_date.html')


# TESTER RESPONSE ========================================================================================================================
@pr_blueprint.route('/test_mail/<no_pr>')
def test_mail(no_pr):
    from app import mysql
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor) #PAKE DICT 

    query_mail = '''
    SELECT 
        no_pr,
        approval_user_id,
        ua.username,
        ua.email 
    FROM pr_approval pa 
    LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
    WHERE no_pr = %s
    '''
    cur.execute(query_mail, [no_pr])
    data_email = cur.fetchall()
    cur.close()
    
    emails = [row['email'] for row in data_email if row['email']]
    email_list = ', '.join(emails)
    
    return email_list
# ====================================================================================================================================
