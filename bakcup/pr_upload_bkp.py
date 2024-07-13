from flask import Blueprint, redirect, render_template, request, session, url_for, flash, jsonify
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

# PR LIST
@pr_blueprint.route('/pr_list')
def pr_list():
    from app import mysql
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM purchase_requisition")
    data = cursor.fetchall()
    cursor.close()
    return render_template('pr/pr_list.html', data=data)


# PR ADD FORM
@pr_blueprint.route('/pr_add')
def pr_add():
    return render_template('pr/pr_add.html')


# SUBMIT PR
@pr_blueprint.route('/pr_submit', methods=['POST'])
def pr_submit():
    from app import mysql
    no_pr = request.form['no_pr']
    username = request.form['username']
    project_name = request.form['project_name']
    entity = request.form['entity']
    total_budget = float(request.form['total_budget'])
    item_name = request.form['item_name']
    item_description = request.form['item_description']
    qty = int(request.form['qty'])
    date_request = datetime.datetime.strptime(request.form['date_request'], '%Y-%m-%d')
    due_date = datetime.datetime.strptime(request.form['due_date'], '%Y-%m-%d')
    created_by = request.form['created_by']
    updated_by = created_by  # samakan updated_at dengan created_at
    approved_by_one = request.form['approved_by_one']
    approved_by_two = request.form['approved_by_two']
    approved_by_three = request.form['approved_by_three']
    approved_by_four = request.form['approved_by_four']

    cursor = mysql.connection.cursor()
    query = '''INSERT INTO purchase_requisition 
               (no_pr, username, project_name, entity, total_budget, item_name, item_description, qty, date_request, due_date, created_by, updated_by, approved_by_one, approved_by_two, approved_by_three, approved_by_four, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())'''
    cursor.execute(query, (no_pr, username, project_name, entity, total_budget, item_name, item_description, qty, date_request, due_date, created_by, updated_by, approved_by_one, approved_by_two, approved_by_three, approved_by_four))
    mysql.connection.commit()
    cursor.close()

    # Assuming create_pdf is a function that generates a PDF
    # create_pdf(no_pr, username, project_name, entity, total_budget, item_name, item_description, qty, date_request, due_date, created_by, approved_by_one, approved_by_two, approved_by_three, approved_by_four)

    return redirect('/pr_list')

# GENERATE PDF PR
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

@pr_blueprint.route('/pr_temp_submit', methods=['GET', 'POST'])
def pr_temp_submit():
    pr_number = None

    # GET ENTITY AND DEPARTMENT
    from app import mysql
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, entity, entity_name FROM entity")
    entities = cursor.fetchall()

    cursor.execute("SELECT id, entity_id, department, department_name FROM department")
    departments = cursor.fetchall()

    cursor.execute("SELECT id, username, email FROM user_accounts")
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

        # INSERT TABLE FOR TABLE PR_HEADER
        insert_header_query = '''
                INSERT INTO pr_header (no_pr ,tanggal_permintaan ,requester_id ,requester_name ,nama_project ,entity ,total_budget_approved ,remarks ,approval1_status ,
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
        cursor.close()
        flash('New PR has been added', 'success')

        return redirect(url_for('pr.pr_list'))
    return render_template('pr/pr_temp.html', pr_number=pr_number, entities=entities, departments=departments, approver=approver)
    


# SEQUENCE PR NUMBER
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

def generate_pr_number(entity, department):
    current_date = datetime.now()
    year_month = current_date.strftime('%y%m')
    sequence_number = f"{get_next_sequence(entity, department):03d}"
    pr_number = f"PR-{entity}-{department}-{year_month}-{sequence_number}"
    
    # from app import mysql
    # cursor = mysql.connection.cursor()
    # try:
    #     cursor.execute("INSERT INTO pr_autonum (entity, department, month, year, pr_no) VALUES (%s, %s, %s, %s, %s)",
    #                    (entity, department, current_date.month, current_date.year, pr_number))
    #     mysql.connection.commit()
    # except MySQLdb.IntegrityError as e:
    #     if e.args[0] == 1062:  # Duplicate entry error
    #         sequence_number = f"{get_next_sequence(entity, department):03d}"
    #         pr_number = f"PR-{entity}-{department}-{year_month}-{sequence_number}"
    #         cursor.execute("INSERT INTO pr_autonum (entity, department, month, year, pr_no) VALUES (%s, %s, %s, %s, %s)",
    #                        (entity, department, current_date.month, current_date.year, pr_number))
    #         mysql.connection.commit()
    # cursor.close()
    return pr_number

@pr_blueprint.route('/generate_pr', methods=['GET', 'POST'])
def generate_pr():
    data = request.json
    entity = data['entity']
    department = data['department']
    pr_number = generate_pr_number(entity, department)
    return jsonify({'pr_number': pr_number})