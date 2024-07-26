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