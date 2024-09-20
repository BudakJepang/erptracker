from flask import Blueprint, redirect, render_template, request, session, url_for, flash, jsonify, current_app, send_file
import os
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta, timezone
from modules.decorator import login_required, check_access
from functools import wraps
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepInFrame, Frame, PageBreak
from reportlab.graphics.shapes import Drawing, Line
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas
from datetime import datetime
from flask_mysqldb import MySQL, MySQLdb
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
from modules.mail import prf_alert_mail, prf_send_approval_manual, prf_alert_mail_done
from modules.logs import insert_pr_log
import socket
import logging
import traceback
from modules.helper import login_required, menu_access_required


# LOCK ADDRESS LOGIN REQUIRED  ____________________________________________________________
# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'loggedin' not in session:
#             next_url = request.url
#             logging.debug(f"Redirecting to login, next URL: {next_url}")
#             return redirect(url_for('auth.login', next=next_url))
#         return f(*args, **kwargs)
#     return decorated_function

# IP ADDRESS
device = socket.gethostname()
ip_address = socket.gethostbyname(device)

# INSERT PR ADD LOGS TABLE  ___________________________________________________________
def insert_pr_log(no_prf, user_id, status, description, ip_address, today):
    from app import mysql
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO prf_logs (no_prf, user_id, status, description, ip_address, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (no_prf, user_id, status, description, ip_address, today)
        )
        mysql.connection.commit()
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        cur.close()
    return "Success insert to log"

def process_and_insert_logs(no_prf, requester_id, ip_address, user_id, functions):
    from app import mysql
    cur = mysql.connection.cursor()
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')   
    
    if functions == 'submit':
        log_mail_user = '''
            SELECT 
                pa.no_prf,
                pa.approval_no,
                pa.approval_user_id,
                ua.username,
                ua.email 
            FROM prf_approval pa 
            LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
            WHERE no_prf = %s
            AND pa.status IS NULL
            ORDER BY 2 ASC
        '''
        cur.execute(log_mail_user, [no_prf])
        logs_mail = cur.fetchall()

        email_descriptions = []
        sender_email = 'procurement@byorange.co.id'
        for log in logs_mail:
            _, _, _, username, email = log
            email_descriptions.append(f'{username} ({email})')

        if email_descriptions:
            # description = f'Sent for signature to {", ".join(email_descriptions)} from {sender_email}'   UNTUK KIRIM MULTIPLE  
            description = f'Sent for signature to {email_descriptions[0]} from {sender_email}'     
            insert_pr_log(no_prf, requester_id, "SENT", description, ip_address, today)
        else:
            pass
    
    elif functions == 'sign':
        log_mail_user = '''
            SELECT 
                pa.no_prf,
                pa.approval_no,
                pa.approval_user_id,
                ua.username,
                ua.email 
            FROM prf_approval pa 
            LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
            WHERE no_prf = %s
            and pa.approval_user_id = %s
            ORDER BY 2 ASC
        '''
        cur.execute(log_mail_user, [no_prf, user_id])
        logs_mail = cur.fetchall()

        log_compeleted = '''
            SELECT DISTINCT status
            FROM prf_approval pa 
            WHERE no_prf = %s
            GROUP BY no_prf
            HAVING COUNT(CASE WHEN status = 'APPROVED' THEN 1 END) = COUNT(*)
        '''
        cur.execute(log_compeleted, [no_prf])
        logs_done = cur.fetchone()

        email_descriptions_app = []
        sender_email = 'procurement@byorange.co.id'
        for log in logs_mail:
            _, _, _, username, email = log
            email_descriptions_app.append(f'{username} ({email})')   
        
        if email_descriptions_app and logs_done:
            first_email_description_app = email_descriptions_app[0]
            description = f'Sign by {first_email_description_app}'
            insert_pr_log(no_prf, requester_id, "SIGNED", description, ip_address, today)
            insert_pr_log(no_prf, requester_id, "COMPLETED", "The document has been completed.", ip_address, today)
            prf_alert_mail_done(no_prf, "data-tech@byorange.co.id", today)
        elif email_descriptions_app:
            first_email_description_app = email_descriptions_app[0]
            description = f'Sign by {first_email_description_app}'
            insert_pr_log(no_prf, requester_id, "SIGNED", description, ip_address, today)
        else:
            pass

    elif functions == 'rejected':
        log_mail_user = '''
            SELECT 
                pa.no_prf,
                pa.approval_no,
                pa.approval_user_id,
                ua.username,
                ua.email 
            FROM prf_approval pa 
            LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
            WHERE no_prf = %s
            and pa.approval_user_id = %s
            ORDER BY 2 ASC
        '''
        cur.execute(log_mail_user, [no_prf, user_id])
        logs_mail = cur.fetchall()

        log_compeleted = '''
            SELECT DISTINCT status
            FROM prf_approval pa 
            WHERE no_prf = %s
            AND status = 'REJECTED'
        '''
        cur.execute(log_compeleted, [no_prf])
        logs_done = cur.fetchone()

        email_descriptions_app = []
        for log in logs_mail:
            _, _, _, username, email = log
            email_descriptions_app.append(f'{username} ({email})')   
        
        if email_descriptions_app:
            first_email_description_app = email_descriptions_app[0]
            description = f'The document has been rejected by {first_email_description_app}'
            insert_pr_log(no_prf, requester_id, "REJECTED", description, ip_address, today)
        else:
            pass

    else:
        pass
             

    cur.close()

# BLUEPRINT AUTH VARIABLE
prf_blueprint = Blueprint('prf', __name__)
# ====================================================================================================================================
current_date = datetime.now()
today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# ====================================================================================================================================
# PRF LIST
# ====================================================================================================================================
@prf_blueprint.route('/prf_list')
@login_required
@menu_access_required(5)
def prf_list():
    from app import mysql
    user_id = session.get('id', 'system')
    if user_id == 'system':
        return redirect(url_for('login'))

    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = '''
            SELECT DISTINCT
            ph.no_prf,
            ph.vendor_name,
            ua2.username,
            d.department_name,
            ph.request_date,
            ph.currency,
            ph.amount,
            GROUP_CONCAT(CONCAT(ua.username, ': ', IFNULL(pa.status, 'PENDING')) ORDER BY pa.approval_no SEPARATOR ', ')AS status 
            FROM prf_header ph 
            LEFT JOIN prf_approval pa ON ph.no_prf  = pa.no_prf 
            LEFT JOIN user_accounts ua ON pa.approval_user_id  = ua.id
            LEFT JOIN user_accounts ua2 ON ph.requester_user_id = ua2.id
            LEFT JOIN department d ON ph.department = d.department 
            WHERE ph.no_prf IN (
                SELECT DISTINCT pa_inner.no_prf
                FROM prf_approval pa_inner
                WHERE pa_inner.approval_user_id = %s OR ph.requester_user_id = %s
            )
            GROUP BY ph.no_prf 
            ORDER BY ph.created_at DESC
        '''
        cur.execute(query, (user_id, user_id))
        data = cur.fetchall()

    except Exception as e:
        traceback.print_exc()
        return "ERROR! while fetching data"

    return render_template('prf/prf_list.html', data=data)
# ====================================================================================================================================



# ====================================================================================================================================
# PRF SUBMIT
# ====================================================================================================================================
def get_prf_number(entity, department):
    current_month = current_date.month
    current_year = current_date.year
    from app import mysql

    cur = mysql.connection.cursor()
    query = '''
        SELECT prf_no FROM prf_autonum
        WHERE entity = %s AND department = %s AND month = %s and year = %s
        ORDER BY created_at DESC LIMIT 1
    '''
    cur.execute(query, (entity, department, current_month, current_year))
    last_prf = cur.fetchone()

    if last_prf:
        last_number = int(last_prf[0].split('-')[-1])
        next_number = last_number + 1
    else:
        next_number = 1

    cur.close()
    return next_number

def generate_prf_number(entity, department):
    year_month = current_date.strftime('%y%m')
    sequence_number = f"{get_prf_number(entity, department):03d}"
    prf_number = f"PRF-{entity}-{department}-{year_month}-{sequence_number}"
    return prf_number

@prf_blueprint.route('/generate_prf', methods = ['GET', 'POST'])
def generate_prf():
    data = request.json
    entity = data['entity']
    department = data['department']
    prf_number = generate_prf_number(entity, department)
    return jsonify({'prf_number': prf_number})

# PRF SUBMIT
@prf_blueprint.route('/prf_add', methods = ['POST', 'GET'])
@login_required
@menu_access_required(5)
def prf_add():
    prf_number = None
    from app import mysql

    user_entities = session.get('entities', [])
    entity_id = [entity['entity_id'] for entity in user_entities]
    cur = mysql.connection.cursor()

    if entity_id:
        cur.execute("SELECT id, entity, entity_name FROM entity WHERE id IN %s", (tuple(entity_id),))
        entities = cur.fetchall()
    else:
        entities = []

    cur.execute("SELECT id, entity_id, department, department_name FROM department WHERE entity_id = 1")
    departments = cur.fetchall()

    cur.execute("SELECT vendor_name, benefeciery_name, bank, no_rekening FROM vendor")
    vendors = cur.fetchall()

    cur.execute("SELECT symbol, iso_code FROM currency")
    currencies = cur.fetchall()

    cur.execute("SELECT id, username, email FROM user_accounts WHERE level = 4")
    approver = cur.fetchall()

    if request.method == 'POST':
        try:
            mysql.connection.begin()

            entity = request.form['entity']
            department = request.form['department']
            no_prf = generate_prf_number(entity, department)
            request_date = request.form['request_date']
            vendor_name = request.form['vendor_name']
            beneficiary_name = request.form['beneficiary_name']
            beneficiary_bank_name = request.form['beneficiary_bank_name']
            beneficiary_bank_number_account = request.form['beneficiary_bank_number_account']
            swift_code_bank = request.form['swift_code_bank']
            currency = request.form['currency']
            amount = request.form['amount']
            supporting_doc_aggreement = request.form['supporting_doc_aggreement']
            supporting_doc_quotation = request.form['supporting_doc_quotation']
            supporting_doc_purchase = request.form['supporting_doc_purchase']
            supporting_doc_invoice = request.form['supporting_doc_invoice']
            supporting_doc_faktur_pajak = request.form['supporting_doc_faktur_pajak']
            supporting_doc_other = request.form['supporting_doc_other']
            description = request.form['description']
            note = request.form['note']
            requester_name = session.get('username', 'system') 
            requester_id = session.get('id', 'system')
            current_date = datetime.now()
            year_month = current_date.strftime('%y%m')

            try:
                cur.execute("INSERT INTO prf_autonum (entity, department, month, year, prf_no) VALUES (%s, %s, %s, %s, %s)",
                (entity, department, current_date.month, current_date.year, no_prf))
            except MySQLdb.IntegrityError as e:
                if e.args[0] == 1062:
                    sequence_number = f"{get_prf_number(entity, department):03d}"
                    prf_number = f"PRF-{entity}-{department}-{year_month}-{sequence_number}"
                    cur.execute("INSERT INTO prf_autonum (entity, department, month, year, prf_no) VALUES (%s, %s, %s, %s, %s)",
                    (entity, department, current_date.month, current_date.year, prf_number))

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

            insert_prf_header = '''
                INSERT INTO prf_header
                (no_prf, vendor_name, beneficiary_name, beneficiary_bank_name, beneficiary_bank_number_account, swift_code_bank, currency, amount, department,
                    supporting_doc_aggreement, supporting_doc_quotation, supporting_doc_purchase, supporting_doc_invoice, supporting_doc_faktur_pajak, supporting_doc_other, description,
                    requester_user_id, request_date, created_by, created_at, updated_by, updated_at, note, entity_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute(insert_prf_header, (no_prf, vendor_name, beneficiary_name, beneficiary_bank_name, beneficiary_bank_number_account, swift_code_bank, currency, amount, department,
                    supporting_doc_aggreement, supporting_doc_quotation, supporting_doc_purchase, supporting_doc_invoice, supporting_doc_faktur_pajak, supporting_doc_other, description,
                    requester_id, request_date, requester_id, today, requester_id, today, note, entity))

            approval_list = []
            id_approval = 1

            while True:
                try:
                    approval_user_id = request.form[f'approval_user_id{id_approval}']
                    approval_list.append((no_prf, id_approval, approval_user_id, None, None, today))
                    id_approval += 1
                except KeyError:
                    break

            if approval_list:
                insert_approval = '''
                    INSERT INTO prf_approval (no_prf, approval_no, approval_user_id, status, notes, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                '''
                cur.executemany(insert_approval, approval_list)

            upload_files = request.files.getlist('files[]')
            upload_docs = []
            for i, file in enumerate(upload_files):
                if file:
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(upload_path)
                    r_path = os.path.relpath(upload_path, 'static')
                    r_path = r_path.replace('\\', '/')
                    upload_docs.append((no_prf, filename, r_path, requester_id, today, requester_id, today))

            if upload_docs:
                insert_docs = '''
                    INSERT INTO prf_docs_reference (no_prf, doc_name, path, created_by, created_at, updated_by, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                '''
                cur.executemany(insert_docs, upload_docs)

            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            query_single_mail = '''
                SELECT 
                    pa.no_prf,
                    pa.approval_no,
                    pa.approval_user_id,
                    ua.username,
                    ua.email,
                    ph.vendor_name,
                    ph.department,
                    ph.amount,
                    e.entity_name
                FROM prf_approval pa 
                LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
                LEFT JOIN prf_header ph ON pa.no_prf = ph.no_prf 
                LEFT JOIN entity e ON ph.entity_id = e.id
                WHERE pa.no_prf = %s
                ORDER BY 2 ASC
                LIMIT 1
            '''
            cur.execute(query_single_mail, [no_prf])
            first_approval_mail = cur.fetchone()
            cur.close()

            mail_approval_recipient = first_approval_mail['email']
            mail_approval_name = first_approval_mail['username']
            mail_vendor_name = first_approval_mail['vendor_name']
            mail_department_name = first_approval_mail['department']
            mail_entity_name = first_approval_mail['entity_name']
            mail_amount = first_approval_mail['amount']
            prf_alert_mail(no_prf, mail_approval_recipient, mail_approval_name, mail_vendor_name, mail_department_name, mail_entity_name, mail_amount, today)
            process_and_insert_logs(no_prf, requester_id, ip_address, None, functions='submit')
            mysql.connection.commit()
            flash('New PRF has been added', 'success')
            return redirect(url_for('prf.prf_list'))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'ERROR PR Failed {e}', 'warning')
            return redirect(url_for('prf.prf_add'))

    return render_template('prf/prf_add.html', prf_number=prf_number, entities=entities, departments=departments, approver=approver, vendors=vendors, currencies=currencies)
# ===========================================================================================================================================================================


# ====================================================================================================================================
# PRF UPDATE
# ====================================================================================================================================
@prf_blueprint.route('/prf_edit/<no_prf>', methods = ['GET', 'POST'])
@login_required
@menu_access_required(5)
def prf_edit(no_prf):
    from app import mysql
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # cur = mysql.connection.cursor()

    user_id = session.get('id', 'system')

    cur.execute('''
        SELECT DISTINCT 
            no_prf,
            vendor_name,
            beneficiary_name,
            beneficiary_bank_name,
            beneficiary_bank_number_account,
            swift_code_bank,
            request_date,
            currency,
            amount,
            department,
            supporting_doc_aggreement,
            supporting_doc_quotation,
            supporting_doc_purchase,
            supporting_doc_invoice,
            supporting_doc_faktur_pajak,
            supporting_doc_other,
            description,
            note
        FROM prf_header ph 
        WHERE no_prf = %s
    ''', (no_prf, ))
    prf_header = cur.fetchone()

    cur.execute('''
        SELECT 
            pa.no_prf,
            pa.approval_no,
            pa.approval_user_id,
            ua.username,
            pa.status,
            pa.notes
        FROM prf_approval pa
        LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id
        WHERE no_prf = %s
    ''', (no_prf, ))
    prf_approval = cur.fetchall()

    cur.execute('''
        SELECT 
            id,
            no_prf,
            doc_name,
            `path`
        FROM prf_docs_reference
        WHERE no_prf = %s
    ''', (no_prf, ))
    prf_documents = cur.fetchall()

    cur.execute("SELECT id, entity_id, department, department_name FROM department WHERE entity_id = 1")
    departments = cur.fetchall()

    cur.execute("SELECT vendor_name, benefeciery_name, bank, no_rekening FROM vendor")
    vendors = cur.fetchall()

    cur.execute("SELECT symbol, iso_code FROM currency")
    currencies = cur.fetchall()

    cur.execute("SELECT id, username, email FROM user_accounts WHERE level = 4")
    approver = cur.fetchall()

    if prf_header is None or prf_approval is None or prf_documents is None:
        flash('PR Not Found', 'warning')
        return redirect(url_for('prf.prf_list'))

    if request.method == 'POST':
        try:
            mysql.connection.begin()
            
            # no_prf = generate_prf_number(entity, department)
            # request_date = request.form['request_date']
            # vendor_name = request.form['vendor_name']
            beneficiary_name = request.form['beneficiary_name']
            beneficiary_bank_name = request.form['beneficiary_bank_name']
            beneficiary_bank_number_account = request.form['beneficiary_bank_number_account']
            swift_code_bank = request.form['swift_code_bank']
            currency = request.form['currency']
            amount = request.form['amount']
            supporting_doc_aggreement = request.form['supporting_doc_aggreement']
            supporting_doc_quotation = request.form['supporting_doc_quotation']
            supporting_doc_purchase = request.form['supporting_doc_purchase']
            supporting_doc_invoice = request.form['supporting_doc_invoice']
            supporting_doc_faktur_pajak = request.form['supporting_doc_faktur_pajak']
            supporting_doc_other = request.form['supporting_doc_other']
            description = request.form['description']
            note = request.form['note']
            requester_id = session.get('id', 'system')
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # year_month = current_date.strftime('%y%m')

            cur.execute('''
                UPDATE prf_header
                SET vendor_name = %s, beneficiary_name = %s, beneficiary_bank_name = %s, beneficiary_bank_number_account = %s, swift_code_bank = %s, 
                currency = %s, amount = %s, supporting_doc_aggreement = %s, supporting_doc_quotation = %s, supporting_doc_purchase = %s, 
                supporting_doc_invoice = %s, supporting_doc_faktur_pajak = %s, supporting_doc_other = %s, description = %s, updated_by = %s, updated_at = %s, note =%s
                WHERE no_prf = %s
            ''', (beneficiary_name, beneficiary_name, beneficiary_bank_name, beneficiary_bank_number_account, swift_code_bank, currency,
                amount, supporting_doc_aggreement, supporting_doc_quotation, supporting_doc_purchase, supporting_doc_invoice, supporting_doc_faktur_pajak, 
                supporting_doc_other, description, requester_id, current_date, note, no_prf))

            cur.execute("SELECT approval_no, approval_user_id, status, notes FROM prf_approval WHERE no_prf = %s ", (no_prf, ))
            existing_appr = cur.fetchall()
            existing_appr_dict = {item['approval_no']: item for item in existing_appr}

            new_appr = []
            id_appr = 1
            while True:
                try:
                    appr_user_id = request.form[f'approval{id_appr}_user_id']
                    new_appr.append((id_appr, appr_user_id))
                    id_appr += 1
                except KeyError:
                    break

            new_appr_dict = {item[0]: item for item in new_appr}

            appr_to_insert = []
            appr_to_update = []
            appr_to_delete = []

            for id_appr, value in new_appr_dict.items():
                if id_appr not in existing_appr_dict:
                    appr_to_insert.append((no_prf, id_appr, value[1], None, None, current_date))
                elif value != existing_appr_dict[id_appr]:
                    appr_to_update.append((value[1], None, None, current_date, no_prf, id_appr))

            for id_appr in existing_appr_dict:
                if id_appr not in new_appr_dict:
                    appr_to_delete.append(id_appr)

            if appr_to_insert:
                insert_query = '''
                    INSERT INTO prf_approval (no_prf, approval_no, approval_user_id, status, notes, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                '''
                cur.executemany(insert_query, appr_to_insert)

            if appr_to_update:
                update_query = '''
                    UPDATE prf_approval
                    SET approval_user_id = %s, status = %s, notes = %s, created_at = %s
                    WHERE no_prf = %s AND approval_no = %s
                '''
                cur.executemany(update_query, appr_to_update)

            if appr_to_delete:
                delete_query = '''
                    DELETE FROM prf_approval
                    WHERE no_prf = %s AND approval_no = %s
                '''
                cur.executemany(delete_query, [(no_prf, index) for index in appr_to_delete])

            upload_files = request.files.getlist('files[]')
            upload_docs = []
            for i, file in enumerate(upload_files):
                if file:
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(upload_path)
                    rel_path = os.path.relpath(upload_path, 'static')
                    rel_path = rel_path.replace('\\', '/')
                    upload_docs.append((no_prf, filename, rel_path, user_id, today, user_id, current_date))

                if upload_docs:
                    insert_docs_query = '''
                        INSERT INTO prf_docs_reference (no_prf, doc_name, path, created_by, created_at, updated_by, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    '''
                    cur.executemany(insert_docs_query, upload_docs)

            file_exist = request.files
            for file_id, file in file_exist.items():
                if file and 'file_exist[' in file_id:
                    actual_file_id = file_id.split('[')[-1][:-1]
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(current_app.config['UPLOAD_PATH'], filename)
                    file.save(upload_path)
                    rel_path = os.path.relpath(upload_path, 'static')
                    rel_path = rel_path.replace('\\', '/')
                    update_docs_query = '''
                        UPDATE prf_docs_reference
                        SET doc_name = %s, path = %s, updated_by = %s, updated_at = %s
                        WHERE id = %s
                    '''
                    cur.execute(update_docs_query, (filename, rel_path, user_id, current_date))

            deleted_files = request.form.getlist('deleted_files[]')
            if deleted_files:
                deleted_docs_query = '''
                    DELETE FROM prf_docs_reference WHERE id IN (%s)
                ''' % ', '.join(['%s'] * len(deleted_files))
                cur.execute(deleted_docs_query, tuple(deleted_files))

            mysql.connection.commit()
            cur.close()
            flash('New PRF has been added', 'success')
            return redirect(url_for('prf.prf_list'))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'ERROR PRF Failed {e}', 'warning')
            return redirect(url_for('prf.prf_edit'))

    return render_template('prf/prf_edit.html', prf_header=prf_header, prf_approval=prf_approval, prf_documents=prf_documents, departments=departments, vendors=vendors, currencies=currencies, approver=approver)
# ====================================================================================================================================


# ====================================================================================================================================
# PRF DETAIL
# ====================================================================================================================================
@prf_blueprint.route('/prf_detail/<no_prf>', methods = ['GET', 'POST'])
@login_required
@menu_access_required(5)
def prf_detail(no_prf):
    from app import mysql
    cur = mysql.connection.cursor()
    current_user_id = session.get('id', 'system')

    query = '''
        SELECT DISTINCT 
            no_prf,
            vendor_name,
            ua.username,
            beneficiary_name,
            beneficiary_bank_name,
            beneficiary_bank_number_account,
            swift_code_bank,
            currency,
            amount,
            d.department_name,
            supporting_doc_aggreement,
            supporting_doc_quotation,
            supporting_doc_purchase,
            supporting_doc_invoice,
            supporting_doc_faktur_pajak,
            supporting_doc_other,
            description,
            request_date,
            c.symbol,
            requester_user_id,
            note,
            e.entity_name,
            e.logo_path
        FROM prf_header ph 
        LEFT JOIN user_accounts ua ON ph.requester_user_id = ua.id 
        LEFT JOIN department d ON ph.department = d.department
        LEFT JOIN currency c ON ph.currency = c.iso_code 
        LEFT JOIN entity e ON ph.entity_id = e.id
        WHERE no_prf = %s
    '''
    cur.execute(query, [no_prf])
    prf_header = cur.fetchall()

    # Ubah tuple menjadi list karena sifat data tupple immutable (untuk replace NL pada form detail)
    prf_header_list = list(prf_header[0])
    prf_header_list[16] = prf_header_list[16].replace("NL", " ")
    prf_header = (tuple(prf_header_list),)  

    # UNTUK REPLACE MULTIPLE TUPLE_______________________
    # prf_header = [list(row) for row in prf_header]
    # for row in prf_header:
    #     row[16] = row[16].replace("NL", " ")
    # prf_header = tuple(tuple(row) for row in prf_header)

    query_approval = """
            SELECT 
                pa.no_prf,
                pa.approval_user_id,
                ua.username,
                pa.status,
                pa.notes,
                pa.approval_no,
                pa.created_at
            FROM prf_approval pa
            LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id
            WHERE no_prf = %s
    """
    cur.execute(query_approval, [no_prf])
    prf_approval = cur.fetchall()

    cur.execute("SELECT DISTINCT no_prf, doc_name, path FROM prf_docs_reference WHERE no_prf = %s", (no_prf,))
    prf_docs = cur.fetchall()

    cur.close()

    return render_template('prf/prf_detail.html', prf_header=prf_header, prf_approval=prf_approval, prf_docs=prf_docs, current_user_id=current_user_id)
# ====================================================================================================================================


# ====================================================================================================================================
# PR DETAIL MANUAL SEND MAIL
# ====================================================================================================================================
@prf_blueprint.route('/prf_send_mail_manual/<approval_id>/<no_prf>', methods=['GET', 'POST'])
@login_required
def prf_send_mail_manual(approval_id, no_prf):
    from app import mysql
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = """
        SELECT DISTINCT 
            ph.no_prf,
            ph.vendor_name,
            ua.username,
            ph.currency,
            ph.amount,
            d.department_name,
            ph.request_date,
            c.symbol,
            ph.requester_user_id,
            e.entity_name,
            pa.approval_user_id,
            ua2.email,
            ua2.username AS approval_name
        FROM prf_header ph 
        LEFT JOIN prf_approval pa ON ph.no_prf = pa.no_prf
        LEFT JOIN user_accounts ua ON ph.requester_user_id = ua.id 
        LEFT JOIN department d ON ph.department = d.department
        LEFT JOIN currency c ON ph.currency = c.iso_code 
        LEFT JOIN entity e ON ph.entity_id = e.id 
        LEFT JOIN user_accounts ua2 ON pa.approval_user_id = ua2.id 
        WHERE ph.no_prf = %s
        AND pa.approval_user_id = %s
    """
    cur.execute(query, [no_prf, approval_id])
    data_email = cur.fetchone()

    
    today = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
    vendor_name = data_email['vendor_name']
    nama_entity = data_email['entity_name']
    department = data_email['department_name']
    nama_requester = data_email['username']
    budget = data_email['amount']
    tanggal_request = data_email['request_date']
    mail_recipient = data_email['email']
    approval_name = data_email['approval_name']

    try:
        prf_send_approval_manual(no_prf, mail_recipient, vendor_name, department, nama_entity, nama_requester, tanggal_request, budget, approval_name, today)
        flash(f'Mail has been sent to {mail_recipient}', 'success')

    except Exception as e:
        print(f"Error :{e}")
        flash(f'Email not sent {e}', 'warning')

    return redirect(url_for('prf.prf_list')) 
    # return f"test kirim ke email: {due_date} approval_name: {approval_name} approval_mail: {mail_recipient}"


# ====================================================================================================================================
# PRF APPROVAL & REJECT
# ====================================================================================================================================
# MAIL APPROVAL________________________________________________________________
def send_sequence_mail_prf(no_prf):

    from app import mysql
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    query = '''
        SELECT DISTINCT
            ph.no_prf,
            pa.approval_no,
            pa.approval_user_id,
            ua.email,
            pa.status,
            ph.vendor_name,
            ph.department,
            ph.amount,
            ua.username,
            e.entity_name
        FROM prf_header ph 
        LEFT JOIN prf_approval pa ON ph.no_prf = pa.no_prf
        LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
        LEFT JOIN entity e ON ph.entity_id = e.id
        WHERE pa.status IS NULL
        AND ph.no_prf = %s
        ORDER BY pa.approval_no ASC
        LIMIT 1
    '''
    cur.execute(query, [no_prf])
    data = cur.fetchone()
    cur.close()

    mail_approval_recipient = data['email'] if data else None
    mail_approval_name = data['username'] if data else None
    mail_vendor_name = data['vendor_name'] if data else None
    mail_department_name = data['department'] if data else None
    mail_entity_name = data['entity_name'] if data else None
    mail_amount = data['amount'] if data else None

    return mail_approval_recipient, mail_approval_name, mail_vendor_name, mail_department_name, mail_entity_name, mail_amount

# APPROVED________________________________________________________________
@prf_blueprint.route('/prf_approved/<no_prf>', methods = ['GET', 'POST'])
@login_required
def prf_approved(no_prf):
    from app import mysql
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        try:
            appr_notes = request.form.get('notes')
            user_id = session.get('id', 'system')

            update_query = f'''
                UPDATE prf_approval
                SET status = 'APPROVED', notes = %s, created_at = NOW()
                WHERE no_prf = %s AND approval_user_id = %s
            '''

            cur.execute(update_query, (appr_notes, no_prf, user_id))
            mail_approval_recipient, mail_approval_name, mail_vendor_name, mail_department_name, mail_entity_name, mail_amount = send_sequence_mail_prf(no_prf)

            if mail_approval_recipient:
                prf_alert_mail(no_prf, mail_approval_recipient, mail_approval_name, mail_vendor_name, mail_department_name, mail_entity_name, mail_amount, today)
                process_and_insert_logs(no_prf, user_id, ip_address, user_id, functions='sign')
                process_and_insert_logs(no_prf, user_id, ip_address, user_id, functions='submit')
            else:
                process_and_insert_logs(no_prf, user_id, ip_address, user_id, functions='sign')
                process_and_insert_logs(no_prf, user_id, ip_address, user_id, functions='submit')
            flash('PRF Approved!', 'success')
            mysql.connection.commit()

        except Exception as e:
            mysql.connection.rollback()
            flash(f'ERROR: {e}', 'warning')

        finally:
            cur.close()
    
    return redirect(url_for('prf.prf_list'))

# REJECTED________________________________________________________________
@prf_blueprint.route('/prf_rejected/<no_prf>', methods = ['GET', 'POST'])
@login_required
@menu_access_required(5)
def prf_rejected(no_prf):
    from app import mysql

    cur = mysql.connection.cursor()
    user_id = session.get('id', 'system')

    if request.method == 'POST':
        try:
            appr_notes = request.form.get('notes')

            update_query = f'''
                UPDATE prf_approval
                SET status = 'REJECTED', notes = %s, created_at = NOW()
                WHERE no_prf = %s AND approval_user_id = %s
            '''

            cur.execute(update_query, (appr_notes, no_prf, user_id))
            process_and_insert_logs(no_prf, user_id, ip_address, user_id, functions='rejected')
            flash('PRF Rejected!', 'success')
            mysql.connection.commit()

        except Exception as e:
            mysql.connection.rollback()
            flash(f'ERROR: {e}', 'warning')

        finally:
            cur.close()
    
    return redirect(url_for('prf.prf_list'))
# ====================================================================================================================================


# ====================================================================================================================================
# PRF GENERATE PDF
# ====================================================================================================================================
@prf_blueprint.route('/prf_generate_pdf/<no_prf>', methods = ['GET', 'POST'])
@login_required
@menu_access_required(5)
def prf_generate_pdf(no_prf):
    from app import mysql
    cur = mysql.connection.cursor()

    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    user_id = session.get('id', 'system')

    cur.execute('''
        SELECT DISTINCT 
            no_prf,
            vendor_name,
            ua.username,
            beneficiary_name,
            beneficiary_bank_name,
            beneficiary_bank_number_account,
            swift_code_bank,
            currency,
            amount,
            d.department_name,
            supporting_doc_aggreement,
            supporting_doc_quotation,
            supporting_doc_purchase,
            supporting_doc_invoice,
            supporting_doc_faktur_pajak,
            supporting_doc_other,
            description,
            request_date,
            c.symbol,
            requester_user_id,
            note,
            e.entity_name,
            e.logo_path,
            ua.sign_path
        FROM prf_header ph 
        LEFT JOIN user_accounts ua ON ph.requester_user_id = ua.id 
        LEFT JOIN department d ON ph.department = d.department
        LEFT JOIN currency c ON ph.currency = c.iso_code 
        LEFT JOIN entity e ON ph.entity_id = e.id 
        WHERE no_prf = %s
    ''', (no_prf, ))

    prf_header = cur.fetchone()

    # GET PRF_APPROVAL
    cur.execute("SELECT sign_path FROM user_accounts WHERE id = %s",(user_id,))
    reqester_ttd = cur.fetchall()

    cur.execute('''
        SELECT 
            pa.no_prf,
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
        FROM prf_approval pa
        LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id
        WHERE no_prf = %s
    ''', (no_prf, ))

    prf_approval = cur.fetchall()

    # LOG PR PDF
    cur.execute('''
    SELECT 
        no_prf,
        status,
        description,
        ip_address ,
        created_at 
    FROM prf_logs pl 
    WHERE no_prf = %s
    ''', (no_prf, ))

    prf_logs = cur.fetchall()


    # pdf code
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize = A4, rightMargin=12, leftMargin=12, topMargin=12, bottomMargin=12)
    elements = []
    styles = getSampleStyleSheet()

    # CUSTOM STYLE
    centered_style = ParagraphStyle(name='centered', alignment=TA_CENTER, fontSize=11, fontName='Times-Roman')
    lefted_style = ParagraphStyle(name='lefted', alignment=TA_LEFT, fontSize=11, fontName='Times-Roman')
    title_style = ParagraphStyle(name='title', alignment=TA_CENTER, fontSize=20, fontName='Times-Bold')
    table_content_style = ParagraphStyle(name='table_content', alignment=TA_RIGHT, fontSize=14, fontName='Times-Bold')
    table_content_style_left = ParagraphStyle(name='table_content_left', alignment=TA_JUSTIFY, fontSize=10, wordWrap='CJK')
    table_header_style = ParagraphStyle(name='table_header', alignment=TA_CENTER, fontSize=11, fontName='Times-Bold')
    log_value_style = ParagraphStyle(name='log_value_style', alignment=TA_CENTER, fontSize=11, fontName='Times-Roman')
    log_value_style_left = ParagraphStyle(name='log_value_style_left', alignment=TA_LEFT, fontSize=11, fontName='Times-Roman')
    footer_style = ParagraphStyle(name='footer', fontSize=11, fontName='Times-Bold')
    name_footer_style = ParagraphStyle(name='footer', fontSize=11, fontName='Times-Bold',  alignment=TA_CENTER)
    detail_key_style = ParagraphStyle(name='detail_key', fontSize=11, fontName='Times-Bold')
    detail_value_style = ParagraphStyle(name='detail_value', fontSize=11, fontName='Times-Roman')
    date_approval = ParagraphStyle(name='footer', fontSize=8, fontName='Times-Roman', alignment=TA_CENTER)

    logo_path = f'static/{prf_header[22]}'
    logo = Image(logo_path, width=3*cm, height=1.3*cm)
    detail_data = [
        [logo, Paragraph('', detail_key_style), Paragraph(f'No. {prf_header[0]}', table_content_style),],
    ]

    # PR HEADER TABLE LIST OUTPUT
    table_detail = Table(detail_data, colWidths=[4.9*inch, 0.2*inch, 2.8*inch])
    table_detail.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    elements.append(table_detail)
    elements.append(Spacer(1, 12))

    # line
    line_data = [
        ['', '', ''],  # Baris kosong untuk padding
        ['', '', ''],  # Baris untuk garis pertama
        # ['', '', ''],  # Baris untuk garis kedua
    ]

    # Tabel line
    line_table = Table(line_data, colWidths=[4.9*inch, 0.2*inch, 2.8*inch])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 1), (-1, 1), 2, colors.black),  # Garis pertama
        ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),  # Garis kedua
        ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Menghilangkan padding kiri
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),  # Menghilangkan padding kanan
        ('BOTTOMPADDING', (0, 0), (-1, 0), -12),  # Padding bawah antara garis
        ('TOPPADDING', (0, 0), (-1, 0), 0),  # Padding atas
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 2))

    # title
    title = Paragraph('Payment Request Form', title_style)
    elements.append(title)
    elements.append(Spacer(1, 14))

    # PR HEADER DATA
    detail_data = [
        [Paragraph('', detail_key_style), Paragraph('', footer_style)],
        [Paragraph('Vendor Name', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{prf_header[1]}', detail_value_style)],
        [Paragraph('Beneficiary Name', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{prf_header[3]}', detail_value_style)],
        [Paragraph('Beneficiary Bank Name', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{prf_header[4]}', detail_value_style)],
        [Paragraph('Beneficiary Bank Number Account', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{prf_header[5]}', detail_value_style)],
        [Paragraph('Swift Code Bank', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{prf_header[6]}', detail_value_style)],
        [Paragraph('Currency and Amount', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{prf_header[18]}. {prf_header[8]:,.2f}', detail_value_style)],
        [Paragraph('Department', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{prf_header[9]}', detail_value_style)],
    ]

    # PR HEADER TABLE LIST OUTPUT
    table_detail = Table(detail_data, colWidths=[2.5*inch, 0.3*inch, 4.9*inch])
    table_detail.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    elements.append(table_detail)
    elements.append(Spacer(1, 17))

    line_data = [
        ['', '', ''], 
        ['', '', ''], 
    ]

    line_table = Table(line_data, colWidths=[4.9*inch, 0.2*inch, 2.8*inch])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 1), (-1, 1), 1, colors.black),  # Garis pertama
        ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),  # Garis kedua
        ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Menghilangkan padding kiri
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),  # Menghilangkan padding kanan
        ('BOTTOMPADDING', (0, 0), (-1, 0), -12),  # Padding bawah antara garis
        ('TOPPADDING', (0, 0), (-1, 0), 0),  # Padding atas
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, -8))

    detail_data = [
    [Paragraph('SUPPORTING DOCUMENTS', detail_key_style)],
    [Paragraph('Agreement', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{prf_header[10]}', detail_value_style)],
    [Paragraph('Quotation', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{prf_header[11]}', detail_value_style)],
    [Paragraph('Purchase Order', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{prf_header[12]}', detail_value_style)],
    [Paragraph('Invoice/Receipt', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{prf_header[13]}', detail_value_style)],
    [Paragraph('Faktur Pajak', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{prf_header[14]}', detail_value_style)],
    [Paragraph('Others (if any)', detail_key_style), Paragraph(':', detail_key_style), Paragraph(f'{prf_header[15]}', detail_value_style)],
]

    table_detail = Table(detail_data, colWidths=[2.5*inch, 0.3*inch, 4.9*inch])
    table_detail.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    elements.append(table_detail)
    elements.append(Spacer(1, 17))

    line_data = [
        ['', '', ''], 
        ['', '', ''], 
    ]

    line_table = Table(line_data, colWidths=[4.9*inch, 0.2*inch, 2.8*inch])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 1), (-1, 1), 1, colors.black),  # Garis pertama
        ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),  # Garis kedua
        ('LEFTPADDING', (0, 0), (-1, -1), 0),  # Menghilangkan padding kiri
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),  # Menghilangkan padding kanan
        ('BOTTOMPADDING', (0, 0), (-1, 0), -12),  # Padding bawah antara garis
        ('TOPPADDING', (0, 0), (-1, 0), 0),  # Padding atas
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, -12))
    
    raw_desc = prf_header[16] 
    descriptions = raw_desc.replace("NL", "<br/>")
    detail_data = [
    # [Paragraph('', detail_key_style)],
    [Paragraph('Descriptions:', detail_key_style)],
    # [Paragraph(f'{prf_header[16]}', detail_value_style)],
    [Paragraph(descriptions, detail_value_style)],
]

    table_detail = Table(detail_data, colWidths=[7.7*inch, 0.3*inch, 4.9*inch])
    table_detail.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    elements.append(table_detail)
    elements.append(Spacer(1, 17))

    # raw text for checking
    # text = """
    #     Dedicated Internet Access Velo <br/>
    #     Period: August, 2024 <br/>
    #     Quantity: 50 Mbps <br/>
    #     Location: Jamsostek Office, Jakarta <br/>
    #     Customer Code: CAP002
    # """
    # prf_header = [
    #     "Dedicated Internet Access Velo Period: August, 2024 Quantity: 50 Mbps Location: Jamsostek Office, Jakarta Customer Code: CAP002"
    # ]

    note_raw = prf_header[20] 
    # MULTIPLE REPLACE OF REPORT
    # formatted_text = text.replace("NL", "<br/>")\
    #                     .replace("NL", "<br/>")\
    #                     .replace("NL", "<br/>")\
    #                     .replace("NL", "<br/>")

    note = note_raw.replace("NL", "<br/>")

    detail_data = [
    [Paragraph('Note:', detail_key_style)],
    [Paragraph(note, detail_value_style)],
    ]

    table_detail = Table(detail_data, colWidths=[7.7*inch, 0.3*inch, 4.9*inch])
    table_detail.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
    ]))
    elements.append(table_detail)
    elements.append(Spacer(1, 18))

    # PR APPROVAL
    styles = getSampleStyleSheet()
    # footer_style = styles['Normal']
    footer_style.alignment = 1  # Center alignment

    # GET REQUESTER APPROVAL NULL OR EXIST SIGN
    requester_sign = prf_header[23] if prf_header[23] else 'static/uploads/white.png'
    # requester_sign = f'static/uploads/white.png'
    signature_image = Image(requester_sign, width=50, height=50)

   # PR APPROVAL SIGNATURE STRUCTURE
    # table_footer_data = [
    #     [Paragraph('Requested by', footer_style), 
    #     Paragraph('Approved by', footer_style), 
    #     Paragraph('Approved by', footer_style), 
    #     Paragraph('Approved by', footer_style), 
    #     Paragraph('Approved by', footer_style)]
    # ]

    table_footer_data = [
        [Paragraph('Requested by', footer_style), 
        Paragraph('Approved by', footer_style), 
        '', '']
    ]

    header_row = [Paragraph('', footer_style),
                Paragraph('Head of Department', footer_style), 
                Paragraph('Head of Finance', footer_style), 
                '',  # Kosong karena kolom Head of Finance span ke kolom ini
                Paragraph('Director', footer_style)]
    table_footer_data.append(header_row)

    # Menambahkan baris kosong antara nama dan tanda tangan
    for x in range(1):  # Sesuaikan jumlah baris jika diperlukan
        table_footer_data.append([Paragraph('', footer_style)] * 5)

    # Tambahkan tanda tangan dan nama requester
    signature_row = [signature_image]
    date_row = [Paragraph(f'{prf_header[17]}', date_approval)]
    approval_row = [Paragraph(f'({prf_header[2]})', footer_style)]

    # Tambahkan tanda tangan, tanggal persetujuan, dan nama approval
    for approval in prf_approval:
        approval_date = str(approval[6]) if str(approval[6]) else ''
        approval_name = f'({approval[3]})' if approval[3] else ''
        sign_path = approval[7] if approval[7] else 'static/uploads/white.png'

        # SIGNATURE DATA
        signature_row.append(Image(sign_path, width=50, height=50))
        # DATE APPROVED
        date_row.append(Paragraph(approval_date, date_approval))
        # APPROVAL NAME DATA
        approval_row.append(Paragraph(approval_name, footer_style))

    # Jika kolom kurang dari 5, tambahkan kolom kosong
    while len(signature_row) < 5:
        signature_row.append(Paragraph('', footer_style))
        date_row.append(Paragraph('', date_approval))
        approval_row.append(Paragraph('', footer_style))

    # Tambahkan baris ke tabel footer
    table_footer_data.append(signature_row)
    table_footer_data.append(date_row)
    table_footer_data.append(approval_row)

    # Buat tabel footer dengan kolom yang sesuai
    table_footer = Table(table_footer_data, colWidths=[1.5 * inch] * 5)
    table_footer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align content to the top
                # Merge "Approved by" dari kolom 2 sampai 5
        ('SPAN', (1, 0), (4, 0)),
        # Merge "Head of Finance" dari kolom 3 sampai 4
        ('SPAN', (2, 1), (3, 1)),
    ]))

    elements.append(table_footer)
    elements.append(Spacer(1, 12))

    # NOT USING MERGE REPORT PDF ONLY_____________________________________
    # doc.build(elements)
    # buffer.seek(0)
    # return send_file(buffer, as_attachment=False, download_name=f'{no_prf}_{current_datetime}.pdf', mimetype='application/pdf')

    # LOGS TRACKER________________________________________________________
    elements.append(PageBreak())
    table_content_style_left_log = ParagraphStyle(name='table_content_left', alignment=TA_CENTER, fontSize=24)
    
    # TITLE LOGS PAGE
    log_title = Paragraph('Document History', table_content_style_left_log)
    elements.append(log_title)
    elements.append(Spacer(1, 28))

    # PR LOGS TABLE HEADER
    logs_table_header = [
        # Paragraph('No', table_header_style),
        Paragraph('Status', table_header_style),
        Paragraph('Description', table_header_style),
        Paragraph('IP Address', table_header_style),
        Paragraph('Datetime', table_header_style)
    ]

    # Append header to table data
    logs_table_data = [logs_table_header]

    # Populate the table with prf_logs data
    for index, log in enumerate(prf_logs):
        if log[1] == 'SENT':
            image = Image('static/entity_logo/sent.png', width=30, height=30)
        elif log[1] == 'SIGNED':
            image = Image('static/entity_logo/signed3.png', width=30, height=30)
        elif log[1] == 'REJECTED':
            image = Image('static/entity_logo/rejection.png', width=30, height=30)
        else:
            image = Image('static/entity_logo/done2.png', width=30, height=30)
        logs_table_data.append([
            # Paragraph(str(index + 1), table_content_style),
            # Image('static/entity_logo/sent.png', width=50, height=50),
            image,
            # Paragraph(log[1], table_content_style),
            Paragraph(log[2], log_value_style_left),
            Paragraph(log[3], log_value_style),
            Paragraph(log[4].strftime('%d %b %Y %H:%M:%S'), log_value_style)
        ])

    # Create table for logs
    # logs_table = Table(logs_table_data, colWidths=[0.5*inch, 1.5*inch, 2.5*inch, 1.5*inch, 2*inch])
    logs_table = Table(logs_table_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2*inch])
    logs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align content to the top
    ]))
    elements.append(logs_table)
    # END LOGS

    # PAGE BREAK AND COMBINE______________________________________________
    doc.build(elements)
    doc.setTitle = 'PRF'
    buffer.seek(0)

    main_pdf = PdfReader(buffer)
    pdf_writer = PdfWriter()

    # list path
    cur.execute("SELECT path FROM prf_docs_reference WHERE no_prf = %s", (no_prf, ))
    add_path = [os.path.join('static', row[0]) for row in cur.fetchall()]
    cur.close()

    for page_num in range(len(main_pdf.pages)):
        pdf_writer.add_page(main_pdf.pages[page_num])

    # convert function
    def convert_img_to_pdf(image_path):
        try:
            img_buffer = BytesIO()
            img_doc = SimpleDocTemplate(img_buffer, pagesize=A4)
            elements = []
            img = Image(image_path)
            img_width, img_height = img.wrap(0,0)
            scale = min(A4[0] / img_width, A4[1] /img_height)
            img.drawWidth = img_width * scale
            img.drawHeight = img_height * scale
            elements.append(img)
            img_doc.build(elements)
            img_buffer.seek(0)
            print(f"Converted image {image_path} to PDF Successfully")
            return img_buffer
        except Exception as e:
            print(f"Error converting {e}")
            return None

    for path in add_path:
        print(f"Processing file: {path}")
        if path.endswith('.pdf'):
            try:
                with open(path, "rb") as f:
                    add_pdf = PdfReader(f)
                    for page_num in range(len(add_pdf.pages)):
                        pdf_writer.add_page(add_pdf.pages[page_num])
                print(f"Added pages form PDF file {path}")
            except Exception as e:
                print(f"Error adding PDF {path}: {e}")
        elif path.endswith('.jpg') or path.endswith('.jpeg') or path.endswith('.png'):
            img_pdf_buffer = convert_img_to_pdf(path)
            if img_pdf_buffer:
                img_pdf = PdfReader(img_pdf_buffer)
                for page_num in range(len(img_pdf.pages)):
                    pdf_writer.add_page(img_pdf.pages[page_num])
                print(f"Added pages from images file: {path}")
            else:
                print(f"Skipping invalid image file: {path}")

    combine_buffer = BytesIO()
    pdf_writer.write(combine_buffer)
    combine_buffer.seek(0)
    print("COMBINE SUCCESSFULLY")

    return send_file(combine_buffer, as_attachment=False, download_name=f'{no_prf}.pdf', mimetype='application/pdf')
# ====================================================================================================================================