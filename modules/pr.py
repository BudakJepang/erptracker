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
from modules.mail import pr_mail, approval_notification_mail



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
            ph.created_at,
            pa.created_at AS approval_date
        FROM pr_header ph 
        LEFT JOIN pr_detail pd ON ph.no_pr = pd.no_pr 
        LEFT JOIN pr_approval pa ON ph.no_pr = pa.no_pr 
        LEFT JOIN entity e ON ph.entity_id = e.id
        WHERE ph.entity_id IN (
        SELECT DISTINCT entity_id
        FROM user_entity WHERE user_id = %s
        )
        AND (ph.requester_id = %s OR pa.approval_user_id = %s)
        GROUP BY 1,2,3,4,5,6,7,8,9,10
        ORDER BY 2 DESC, 1 DESC
        '''
        cursor.execute(query, (user_id, user_id, user_id))
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

    # GET USER_ID FROM LOGIN SESSION
    current_user_id = session.get('id', 'system')

    # QUERY LIST FOR PR_HEADER DATA
    query = """
            SELECT DISTINCT 
                ph.no_pr,
                ph.tanggal_permintaan,
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
            ORDER BY 2 DESC
    """
    cur.execute(query, [no_pr])
    pr_header = cur.fetchall()
    
    # Log data for debugging
    logging.debug(f"Data fetched for no_pr {no_pr}: {pr_header}")

    # QUERY LIST FOR PR_DETAIL
    cur.execute("SELECT no_pr, item_no, nama_item, spesifikasi, qty, tanggal FROM pr_detail WHERE no_pr = %s", (no_pr,))
    pr_detail = cur.fetchall()

    # QUERY LIST FOR APPROVAL
    query_approval = """
            SELECT 
                pa.no_pr,
                pa.approval_user_id,
                ua.username,
                pa.status,
                pa.notes,
                pa.created_at
            FROM pr_approval pa
            LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id
            WHERE no_pr = %s
    """
    cur.execute(query_approval, [no_pr])
    pr_approval = cur.fetchall()

    cur.close()

    return render_template('pr/pr_detail.html', pr_header=pr_header, pr_detail=pr_detail, pr_approval=pr_approval, current_user_id=current_user_id)


# PR APPROVED
def send_sequence_mail_pr(no_pr):
    from app import mysql
    cur = mysql.connection.cursor()

    query = '''
        SELECT DISTINCT
            ph.no_pr,
            pa.approval_user_id,
            ua.email,
            pa.status 
        FROM pr_header ph 
        LEFT JOIN pr_approval pa ON ph.no_pr = pa.no_pr
        LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
        WHERE pa.status is null
        AND ph.no_pr = %s
        LIMIT 1
    '''
    cur.execute(query, [no_pr])
    data = cur.fetchone()
    cur.close()
    email = data['email']
    print(f'=============================== INI TUH PRINT EMAIL {email}')
    return email

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
            email = 'rohmankpai@gmail.com'
            requestName = 'Mohammad Nurohman'
            approvalName = 'David Irwan'
            entityName = 'PT. ORANGE INOVASI DIGITAL'
            budget = "2000000"
            dueDate = '2024-08-01'
            print(f'INI PRINT EMAILL CUUYYYY -=========================== {email}')
            pr_mail(no_pr, email, requestName, approvalName, budget, dueDate, entityName)
            flash('PR has been approved successfully!', 'success')

        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error: {str(e)}', 'danger')
        finally:
            cur.close()
    
    return redirect(url_for('pr.pr_list')) 
