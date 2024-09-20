from flask import Blueprint, redirect, render_template, request, session, url_for, flash, jsonify, current_app, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from modules.time import convert_time_to_wib
from datetime import datetime, timedelta, timezone
from modules.decorator import login_required, check_access
from functools import wraps
from flask_mysqldb import MySQLdb
import traceback
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
from modules.mail import woc_alert_mail, woc_send_approval_manual, woc_alert_mail_done
import socket
from modules.helper import login_required


# IP ADDRESS
device = socket.gethostname()
ip_address = socket.gethostbyname(device)
current_date = datetime.now()
today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# BLUEPRINT VENDOR VARIABLE
woc_blueprint = Blueprint('woc', __name__)

# INSERT WOC ADD LOGS TABLE  ___________________________________________________________
def insert_woc_log(no_woc, user_id, status, description, ip_address, today):
    from app import mysql
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO woc_logs (no_woc, user_id, status, description, ip_address, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (no_woc, user_id, status, description, ip_address, today)
        )
        mysql.connection.commit()
    except Exception as e:
        print(f'Error: {str(e)}')
    finally:
        cur.close()
    return "Success insert to log"

def process_and_insert_logs(no_woc, requester_id, ip_address, user_id, functions):
    from app import mysql
    cur = mysql.connection.cursor()
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')   
    
    if functions == 'submit':
        log_mail_user = '''
            SELECT 
                pa.no_woc,
                pa.approval_no,
                pa.approval_user_id,
                ua.username,
                ua.email 
            FROM woc_approval pa 
            LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
            WHERE no_woc = %s
            AND pa.status IS NULL
            ORDER BY 2 ASC
        '''
        cur.execute(log_mail_user, [no_woc])
        logs_mail = cur.fetchall()

        email_descriptions = []
        sender_email = 'procurement@byorange.co.id'
        for log in logs_mail:
            _, _, _, username, email = log
            email_descriptions.append(f'{username} ({email})')

        if email_descriptions:
            # description = f'Sent for signature to {", ".join(email_descriptions)} from {sender_email}'   UNTUK KIRIM MULTIPLE  
            description = f'Sent for signature to {email_descriptions[0]} from {sender_email}'     
            insert_woc_log(no_woc, requester_id, "SENT", description, ip_address, today)
        else:
            pass
    
    elif functions == 'sign':
        log_mail_user = '''
            SELECT 
                pa.no_woc,
                pa.approval_no,
                pa.approval_user_id,
                ua.username,
                ua.email 
            FROM woc_approval pa 
            LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
            WHERE no_woc = %s
            and pa.approval_user_id = %s
            ORDER BY 2 ASC
        '''
        cur.execute(log_mail_user, [no_woc, user_id])
        logs_mail = cur.fetchall()

        log_compeleted = '''
            SELECT DISTINCT status
            FROM woc_approval pa 
            WHERE no_woc = %s
            GROUP BY no_woc
            HAVING COUNT(CASE WHEN status = 'APPROVED' THEN 1 END) = COUNT(*)
        '''
        cur.execute(log_compeleted, [no_woc])
        logs_done = cur.fetchone()

        email_descriptions_app = []
        sender_email = 'procurement@byorange.co.id'
        for log in logs_mail:
            _, _, _, username, email = log
            email_descriptions_app.append(f'{username} ({email})')   
        
        if email_descriptions_app and logs_done:
            first_email_description_app = email_descriptions_app[0]
            description = f'Sign by {first_email_description_app}'
            insert_woc_log(no_woc, requester_id, "SIGNED", description, ip_address, today)
            insert_woc_log(no_woc, requester_id, "COMPLETED", "The document has been completed.", ip_address, today)
            woc_alert_mail_done(no_woc, mail_recipient="mohammad.nurohman@byorange.co.id")
        elif email_descriptions_app:
            first_email_description_app = email_descriptions_app[0]
            description = f'Sign by {first_email_description_app}'
            insert_woc_log(no_woc, requester_id, "SIGNED", description, ip_address, today)
        else:
            pass

    elif functions == 'rejected':
        log_mail_user = '''
            SELECT 
                pa.no_woc,
                pa.approval_no,
                pa.approval_user_id,
                ua.username,
                ua.email 
            FROM woc_approval pa 
            LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
            WHERE no_woc = %s
            and pa.approval_user_id = %s
            ORDER BY 2 ASC
        '''
        cur.execute(log_mail_user, [no_woc, user_id])
        logs_mail = cur.fetchall()

        log_compeleted = '''
            SELECT DISTINCT status
            FROM woc_approval pa 
            WHERE no_woc = %s
            AND status = 'REJECTED'
        '''
        cur.execute(log_compeleted, [no_woc])
        logs_done = cur.fetchone()

        email_descriptions_app = []
        for log in logs_mail:
            _, _, _, username, email = log
            email_descriptions_app.append(f'{username} ({email})')   
        
        if email_descriptions_app:
            first_email_description_app = email_descriptions_app[0]
            description = f'The document has been rejected by {first_email_description_app}'
            insert_woc_log(no_woc, requester_id, "REJECTED", description, ip_address, today)
        else:
            pass

    else:
        pass

    cur.close()
# ================================================================================================================

# ====================================================================================================================================
# WOC LIST
# ====================================================================================================================================
@woc_blueprint.route('/woc_list')
@login_required
def woc_list():
    from app import mysql
    user_id = session.get('id', 'system')
    try:
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = '''
            SELECT DISTINCT
            wh.no_woc,
            v.benefeciery_name,
            wh.requester_name,
            e.entity_name,
            d.department_name,
            wh.request_date,
            wh.description,
            wh.reason,
            GROUP_CONCAT(CONCAT(ua.username, ': ', IFNULL(pa.status, 'PENDING')) ORDER BY pa.approval_no SEPARATOR ', ')AS status 
            FROM woc_header wh 
            LEFT JOIN woc_approval pa ON wh.no_woc  = pa.no_woc 
            LEFT JOIN user_accounts ua ON pa.approval_user_id  = ua.id
            LEFT JOIN department d ON wh.department = d.department 
            LEFT JOIN vendor v ON wh.vendor_id = v.id
            LEFT JOIN entity e ON wh.entity_id = e.id
            WHERE wh.no_woc  IN (
                SELECT DISTINCT pa_inner.no_woc
                FROM woc_approval pa_inner
                WHERE pa_inner.approval_user_id = %s OR wh.created_by  = %s
            )
            GROUP BY wh.no_woc
            ORDER BY wh.created_at DESC
        '''
        cur.execute(query, (user_id, user_id))
        data = cur.fetchall()
    except Exception as e:
        traceback.print_exc()
        return "ERRROR! while fetching data {e}"
    return render_template('woc/woc_list.html', data=data)
# ====================================================================================================================================



# ====================================================================================================================================
# WOC ADD / SUBMIT 
# ====================================================================================================================================
def get_woc_number(entity, department):
    current_month = current_date.month
    current_year = current_date.year
    from app import mysql

    cur = mysql.connection.cursor()
    query = '''
        SELECT woc_no FROM woc_autonum
        WHERE entity = %s AND department = %s AND month = %s and year = %s
        ORDER BY created_at DESC LIMIT 1
    '''
    cur.execute(query, (entity, department, current_month, current_year))
    last_woc = cur.fetchone()

    if last_woc:
        last_number = int(last_woc[0].split('-')[-1])
        next_number = last_number + 1
    else:
        next_number = 1

    cur.close()
    return next_number

def generate_woc_number(entity, department):
    year_month = current_date.strftime('%y%m')
    sequence_number = f"{get_woc_number(entity, department):03d}"
    woc_number = f"WOC-{entity}-{department}-{year_month}-{sequence_number}"
    return woc_number

@woc_blueprint.route('/generate_woc', methods = ['GET', 'POST'])
def generate_woc():
    data = request.json
    entity = data['entity']
    department = data['department']
    woc_number = generate_woc_number(entity, department)
    return jsonify({'woc_number': woc_number})

@woc_blueprint.route('/woc_add', methods = ['GET', 'POST'])
@login_required
def woc_add():
    woc_number = None
    from app import mysql
    cur = mysql.connection.cursor()

    user_entities = session.get('entities', [])
    entity_id = [entity['entity_id'] for entity in user_entities]

    if entity_id:
        cur.execute("SELECT id, entity, entity_name FROM entity WHERE id IN %s", (tuple(entity_id),))
        entities = cur.fetchall()
    else:
        entities = []

    cur.execute("SELECT id, entity_id, department, department_name FROM department WHERE entity_id = 1")
    departments = cur.fetchall()

    cur.execute("SELECT id, vendor_name, benefeciery_name, bank, no_rekening FROM vendor")
    vendors = cur.fetchall()

    cur.execute("SELECT id, username, email FROM user_accounts WHERE level = 4")
    approver = cur.fetchall()

    if request.method == 'POST':
        try:
            mysql.connection.begin()

            entity = request.form['entity']
            department = request.form['department']
            no_woc = generate_woc_number(entity, department)
            request_date = request.form['request_date']
            requester_name = request.form['requester_name']
            vendor = request.form['vendor']
            desc = request.form['description']
            reason = request.form['reason']
            current_date = datetime.now()
            year_month = current_date.strftime("%y%m")
            requester_id = session.get('id', 'system')

            try:
                cur.execute("INSERT INTO woc_autonum (entity, department, month, year, woc_no) VALUES (%s, %s, %s, %s, %s)",
                (entity, department, current_date.month, current_date.year, no_woc))
            except MySQLdb.IntegrityError as e:
                if e.args[0] == 1062:
                    sequence_number = f"{get_woc_number(entity, department):03d}"
                    woc_number = f"WOC-{entity}-{department}-{year_month}-{sequence_number}"
                    cur.execute("INSERT INTO woc_autonum (entity, department, month, year, woc_no) VALUES (%s, %s, %s, %s, %s)",
                    (entity, department, current_date.month, current_date.year, woc_number))

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

            
            insert_woc_header = '''
                INSERT INTO woc_header
                (no_woc, requester_name, department, vendor_id, entity_id, description, reason, request_date, created_by, created_at, updated_by, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute(insert_woc_header, (no_woc, requester_name, department, vendor, entity, desc, reason, request_date, requester_id, today, requester_id, today))

            approval_list = []
            id_approval = 1

            while True:
                try:
                    approval_user_id = request.form[f'approval_user_id{id_approval}']
                    approval_list.append((no_woc, id_approval, approval_user_id, None, None, today))
                    id_approval += 1
                except KeyError:
                    break

            if approval_list:
                insert_approval = '''
                    INSERT INTO woc_approval (no_woc, approval_no, approval_user_id, status, notes, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                '''
                cur.executemany(insert_approval, approval_list)
            
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            query_single_mail = '''
                SELECT 
                    pa.no_woc,
                    pa.approval_no,
                    pa.approval_user_id,
                    ua.username,
                    ua.email,
                    wh.requester_name,
                    wh.department,
                    wh.description,
                    e.entity_name,
                    v.vendor_name
                FROM woc_approval pa 
                LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
                LEFT JOIN woc_header wh ON pa.no_woc = wh.no_woc
                LEFT JOIN entity e ON wh.entity_id = e.id
                LEFT JOIN vendor v ON wh.vendor_id = v.id
                WHERE pa.no_woc = %s
                ORDER BY 2 ASC
                LIMIT 1
            '''
            cur.execute(query_single_mail, [no_woc])
            first_approval_mail = cur.fetchone()
            cur.close()

            mail_approval_recipient = first_approval_mail['email']
            mail_approval_name = first_approval_mail['username']
            mail_approval_reqester = first_approval_mail['requester_name']
            mail_approval_desc = first_approval_mail['description']
            mail_approval_entity = first_approval_mail['entity_name']
            mail_approval_vendor = first_approval_mail['vendor_name']
            woc_alert_mail(no_woc, mail_approval_recipient, mail_approval_name, mail_approval_reqester, mail_approval_desc, mail_approval_entity, mail_approval_vendor, today)
            process_and_insert_logs(no_woc, requester_id, ip_address, None, functions='submit')

            flash("New WOC Has been added", 'success')
            mysql.connection.commit()
            return redirect(url_for('woc.woc_list'))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'ERROR WOC Failed {e}', 'warning')
            return redirect(url_for('woc.woc_add'))
    
    cur.close()
    return render_template('woc/woc_add.html', woc_number=woc_number, entities=entities, departments=departments, approver=approver, vendors=vendors)
# ====================================================================================================================================

        
# ====================================================================================================================================
# WOC DETAIL
# ====================================================================================================================================
@woc_blueprint.route('/woc_detail/<no_woc>', methods = ['GET', 'POST'])
@login_required
def woc_detail(no_woc):
    from app import mysql
    cur = mysql.connection.cursor()
    current_user_id = session.get('id', 'system')

    query = '''
        SELECT DISTINCT 
            wh.no_woc,
            wh.requester_name,
            v.vendor_name,
            e.entity_name,
            d.department_name,
            wh.description,
            wh.reason,
            wh.request_date,
            ua.username,
            wh.created_by
            FROM woc_header wh 
        LEFT JOIN entity e ON wh.entity_id = id 
        LEFT JOIN department d ON wh.department = d.department 
        LEFT JOIN user_accounts ua ON wh.created_by = ua.id 
        LEFT JOIN vendor v ON wh.vendor_id = v.id
        WHERE wh.no_woc = %s
    '''
    cur.execute(query, [no_woc])
    woc_header = cur.fetchall()

    # woc_header = [list(row) for row in woc_header]
    # for row in woc_header:
    #     row[7] = row[7].replace("NL", " ")
    #     row[8] = row[8].replace("NL", " ")
    # woc_header = tuple(tuple(row) for row in woc_header)


    query_approval = """
            SELECT 
                pa.no_woc,
                pa.approval_user_id,
                ua.username,
                pa.status,
                pa.notes,
                pa.approval_no,
                pa.created_at
            FROM woc_approval pa
            LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id
            WHERE no_woc = %s
    """
    cur.execute(query_approval, [no_woc])
    woc_approval = cur.fetchall()

    cur.close()
    return render_template('woc/woc_detail.html', woc_header=woc_header, woc_approval=woc_approval, current_user_id=current_user_id)
    # return f'{current_user_id}'
# ====================================================================================================================================



# ====================================================================================================================================
# WOC UPDATE
# ====================================================================================================================================
@woc_blueprint.route('/woc_edit/<no_woc>', methods = ['GET', 'POST'])
@login_required
def woc_edit(no_woc):
    from app import mysql
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cur.execute('''
        SELECT DISTINCT
            no_woc,
            requester_name,
            request_date,
            vendor_id,
            v.vendor_name,
            description,
            reason
        FROM woc_header wh
        LEFT JOIN vendor v ON wh.vendor_id = v.id
        WHERE no_woc = %s
    ''', (no_woc, ))
    woc_header = cur.fetchone()

    cur.execute('''
        SELECT 
            pa.no_woc,
            pa.approval_no,
            pa.approval_user_id,
            ua.username,
            pa.status,
            pa.notes
        FROM woc_approval pa
        LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id
        WHERE no_woc = %s
    ''', (no_woc, ))
    woc_approval = cur.fetchall()

    cur.execute("SELECT id, vendor_name, benefeciery_name, bank, no_rekening FROM vendor")
    vendors = cur.fetchall()

    cur.execute("SELECT id, username, email FROM user_accounts WHERE level = 4")
    approver = cur.fetchall()

    if woc_header is None or woc_approval is None :
        flash('WOC Not Found', 'warning')
        return redirect(url_for('woc.woc_list'))

    if request.method == 'POST':
        try:
            mysql.connection.begin()
            
            vendor = request.form['beneficiary_name']
            requester_name = request.form['requester_name']
            description = request.form['description']
            reason = request.form['reason']
            requester_id = session.get('id', 'system')
            current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # year_month = current_date.strftime('%y%m')

            cur.execute('''
                UPDATE woc_header
                SET vendor_id = %s, requester_name = %s, description = %s, reason = %s, updated_by = %s, updated_at = %s
                WHERE no_woc = %s
            ''', (vendor, requester_name, description, reason, requester_id, current_date, no_woc))

            cur.execute("SELECT approval_no, approval_user_id, status, notes FROM woc_approval WHERE no_woc = %s ", (no_woc, ))
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
                    appr_to_insert.append((no_woc, id_appr, value[1], None, None, current_date))
                elif value != existing_appr_dict[id_appr]:
                    appr_to_update.append((value[1], None, None, current_date, no_woc, id_appr))

            for id_appr in existing_appr_dict:
                if id_appr not in new_appr_dict:
                    appr_to_delete.append(id_appr)

            if appr_to_insert:
                insert_query = '''
                    INSERT INTO woc_approval (no_woc, approval_no, approval_user_id, status, notes, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                '''
                cur.executemany(insert_query, appr_to_insert)

            if appr_to_update:
                update_query = '''
                    UPDATE woc_approval
                    SET approval_user_id = %s, status = %s, notes = %s, created_at = %s
                    WHERE no_woc = %s AND approval_no = %s
                '''
                cur.executemany(update_query, appr_to_update)

            if appr_to_delete:
                delete_query = '''
                    DELETE FROM woc_approval
                    WHERE no_woc = %s AND approval_no = %s
                '''
                cur.executemany(delete_query, [(no_woc, index) for index in appr_to_delete])

            mysql.connection.commit()
            cur.close()
            flash('WOC has been saved', 'success')
            return redirect(url_for('woc.woc_list'))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'ERROR WOC Edit Failed {e}', 'warning')
            return redirect(url_for('woc.woc_edit'))

    return render_template('woc/woc_edit.html', woc_header=woc_header, woc_approval=woc_approval,  vendors=vendors, approver=approver)
# ====================================================================================================================================


# ====================================================================================================================================
# PR DETAIL MANUAL SEND MAIL
# ====================================================================================================================================
@woc_blueprint.route('/woc_send_mail_manual/<approval_id>/<no_woc>', methods=['GET', 'POST'])
@login_required
def woc_send_mail_manual(approval_id, no_woc):
    from app import mysql
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = """
        SELECT DISTINCT 
            wh.no_woc,
            wh.requester_name,
            v.vendor_name,
            e.entity_name,
            d.department_name,
            wh.description,
            wh.reason,
            wh.request_date,
            ua.username,
            wh.created_by,
            ua2.username AS approval_name,
            ua2.email
            FROM woc_header wh 
        LEFT JOIN entity e ON wh.entity_id = id 
        LEFT JOIN department d ON wh.department = d.department 
        LEFT JOIN user_accounts ua ON wh.created_by = ua.id 
        LEFT JOIN vendor v ON wh.vendor_id = v.id
        LEFT JOIN woc_approval wa ON wh.no_woc = wa.no_woc
        LEFT JOIN user_accounts ua2 ON wa.approval_user_id = ua2.id
        WHERE wh.no_woc = %s
        AND wa.approval_user_id = %s
    """
    cur.execute(query, [no_woc, approval_id])
    data_email = cur.fetchone()

    
    today = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
    vendor_name = data_email['vendor_name']
    nama_entity = data_email['entity_name']
    department = data_email['department_name']
    nama_requester = data_email['username']
    description = data_email['description']
    tanggal_request = data_email['request_date']
    mail_recipient = data_email['email']
    approval_name = data_email['approval_name']

    try:
        woc_send_approval_manual(no_woc, mail_recipient, vendor_name, department, nama_entity, nama_requester, tanggal_request, description, approval_name, today)
        flash(f'Mail has been sent to {mail_recipient}', 'success')

    except Exception as e:
        print(f"Error :{e}")
        flash(f'Email not sent {e}', 'warning')

    return redirect(url_for('woc.woc_list')) 
    # return f"test kirim ke email: {due_date} approval_name: {approval_name} approval_mail: {mail_recipient}"

# ====================================================================================================================================
# WOC APPROVAL & REJECT
# ====================================================================================================================================
# MAIL APPROVAL________________________________________________________________
def send_sequence_mail_woc(no_woc):

    from app import mysql
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    query = '''
        SELECT DISTINCT
            ph.no_woc,
            pa.approval_no,
            pa.approval_user_id,
            ua.email,
            pa.status,
            ua.username,
            ph.requester_name,
            v.vendor_name,
            e.entity_name,
            ph.description
        FROM woc_header ph 
        LEFT JOIN woc_approval pa ON ph.no_woc = pa.no_woc
        LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id 
        LEFT JOIN vendor v ON ph.vendor_id = v.id
        LEFT JOIN entity e ON ph.entity_id = e.id
        WHERE pa.status IS NULL
        AND ph.no_woc = %s
        ORDER BY approval_no DESC
        LIMIT 1
    '''
    cur.execute(query, [no_woc])
    data = cur.fetchone()
    cur.close()

    mail_approval_recipient = data['email'] if data else None
    mail_approval_name = data['username'] if data else None
    mail_approval_desc = data['description'] if data else None
    mail_approval_entity = data['entity_name'] if data else None
    mail_approval_vendor = data['vendor_name'] if data else None
    mail_approval_reqester = data['requester_name'] if data else None

    return mail_approval_recipient, mail_approval_name, mail_approval_desc, mail_approval_entity, mail_approval_vendor, mail_approval_reqester


# APPROVED________________________________________________________________
@woc_blueprint.route('/woc_approved/<no_woc>', methods = ['GET', 'POST'])
@login_required
def woc_approved(no_woc):
    from app import mysql
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        try:
            appr_notes = request.form.get('notes')
            user_id = session.get('id', 'system')

            update_query = f'''
                UPDATE woc_approval
                SET status = 'APPROVED', notes = %s, created_at = NOW()
                WHERE no_woc = %s AND approval_user_id = %s
            '''

            cur.execute(update_query, (appr_notes, no_woc, user_id))
            mail_approval_recipient, mail_approval_name, mail_approval_desc, mail_approval_entity, mail_approval_vendor, mail_approval_reqester = send_sequence_mail_woc(no_woc)

            if mail_approval_recipient:
                woc_alert_mail(no_woc, mail_approval_recipient, mail_approval_name, mail_approval_reqester, mail_approval_desc, mail_approval_entity, mail_approval_vendor, today)
                # woc_alert_mail(no_woc, mail_next_approval)
                process_and_insert_logs(no_woc, user_id, ip_address, user_id, functions='sign')
                process_and_insert_logs(no_woc, user_id, ip_address, user_id, functions='submit')
            else:
                process_and_insert_logs(no_woc, user_id, ip_address, user_id, functions='sign')
                process_and_insert_logs(no_woc, user_id, ip_address, user_id, functions='submit')
            flash('WOC Approved!', 'success')
            mysql.connection.commit()

        except Exception as e:
            mysql.connection.rollback()
            flash(f'ERROR: {e}', 'warning')

        finally:
            cur.close()
    
    return redirect(url_for('woc.woc_list'))

# REJECTED________________________________________________________________
@woc_blueprint.route('/woc_rejected/<no_woc>', methods = ['GET', 'POST'])
@login_required
def woc_rejected(no_woc):
    from app import mysql

    cur = mysql.connection.cursor()
    user_id = session.get('id', 'system')

    if request.method == 'POST':
        try:
            appr_notes = request.form.get('notes')

            update_query = f'''
                UPDATE woc_approval
                SET status = 'REJECTED', notes = %s, created_at = NOW()
                WHERE no_woc = %s AND approval_user_id = %s
            '''

            cur.execute(update_query, (appr_notes, no_woc, user_id))
            process_and_insert_logs(no_woc, user_id, ip_address, user_id, functions='rejected')
            flash('WOC Rejected!', 'success')
            mysql.connection.commit()

        except Exception as e:
            mysql.connection.rollback()
            flash(f'ERROR: {e}', 'warning')

        finally:
            cur.close()
    
    return redirect(url_for('woc.woc_list'))
# ====================================================================================================================================


# ====================================================================================================================================
# GENERATE WOC PDF
# ====================================================================================================================================
@woc_blueprint.route('/woc_generate_pdf/<no_woc>', methods = ['GET', 'POST'])
@login_required
def woc_generate_pdf(no_woc):
    from app import mysql
    cur = mysql.connection.cursor()

    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # current_date = datetime.now().strftime('%Y-%m-%d')
    user_id = session.get('id', 'system')

    cur.execute('''
        SELECT DISTINCT 
            wh.no_woc,
            wh.requester_name,
            v.vendor_name,
            e.entity_name,
            d.department_name,
            wh.description,
            wh.reason,
            wh.request_date,
            ua.username
            FROM woc_header wh 
        LEFT JOIN entity e ON wh.entity_id = id 
        LEFT JOIN department d ON wh.department = d.department 
        LEFT JOIN user_accounts ua ON wh.created_by = ua.id 
        LEFT JOIN vendor v ON wh.vendor_id = v.id
        WHERE wh.no_woc = %s
    ''', (no_woc, ))

    woc_header = cur.fetchone()

    # GET WOC_APPROVAL
    cur.execute("SELECT sign_path FROM user_accounts WHERE id = %s",(user_id,))
    reqester_ttd = cur.fetchall()

    cur.execute('''
        SELECT 
            pa.no_woc,
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
        FROM woc_approval pa
        LEFT JOIN user_accounts ua ON pa.approval_user_id = ua.id
        WHERE no_woc = %s
    ''', (no_woc, ))

    woc_approval = cur.fetchall()

    # LOG PR PDF
    cur.execute('''
    SELECT 
        no_woc,
        status,
        description,
        ip_address ,
        created_at 
    FROM woc_logs
    WHERE no_woc = %s
    ''', (no_woc, ))

    woc_logs = cur.fetchall()


    # pdf code
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize = A4, rightMargin=45, leftMargin=45, topMargin=72, bottomMargin=32)
    elements = []
    styles = getSampleStyleSheet()

    # CUSTOM STYLE
    centered_style = ParagraphStyle(name='centered', alignment=TA_CENTER, fontSize=11, fontName='Times-Roman')
    lefted_style = ParagraphStyle(name='lefted', alignment=TA_LEFT, fontSize=11, fontName='Times-Bold')
    title_style = ParagraphStyle(name='title', alignment=TA_CENTER, fontSize=16, fontName='Times-Bold')
    table_content_style = ParagraphStyle(name='table_content', alignment=TA_RIGHT, fontSize=14, fontName='Times-Bold')
    table_content_style_left = ParagraphStyle(name='table_content_left', alignment=TA_JUSTIFY, fontSize=10, wordWrap='CJK')
    table_header_style = ParagraphStyle(name='table_header', alignment=TA_CENTER, fontSize=11, fontName='Times-Bold')
    log_value_style = ParagraphStyle(name='log_value_style', alignment=TA_CENTER, fontSize=11, fontName='Times-Roman')
    footer_style = ParagraphStyle(name='footer', fontSize=11, fontName='Times-Bold')
    name_footer_style = ParagraphStyle(name='footer', fontSize=11, fontName='Times-Bold',  alignment=TA_CENTER)
    detail_key_style = ParagraphStyle(name='detail_key', fontSize=11, fontName='Times-Bold')
    detail_value_style = ParagraphStyle(name='detail_value', fontSize=11, alignment=TA_JUSTIFY, fontName = 'Times-Roman', spaceBefore=35, spaceAfter=35)
    date_approval = ParagraphStyle(name='footer', fontSize=8, fontName='Times-Roman', alignment=TA_CENTER)

    # title
    title = Paragraph('Waiver of Competition Form (WOC)', title_style)
    elements.append(title)
    elements.append(Spacer(1, 44))

    title = Paragraph('Data yang harus dilengkapi oleh pemohon :', lefted_style)
    elements.append(title)
    elements.append(Spacer(1, 1))

    # PR HEADER DATA
    detail_data = [
        [Paragraph('', detail_key_style), Paragraph('', footer_style)],
        [Paragraph('Tanggal', detail_value_style), Paragraph(':', detail_key_style), Paragraph(f'{woc_header[7].strftime("%d %B %Y")}', detail_value_style)],
        [Paragraph('Nama Pemohon', detail_value_style), Paragraph(':', detail_key_style), Paragraph(f'{woc_header[1]}', detail_value_style)],
        [Paragraph('Department', detail_value_style), Paragraph(':', detail_key_style), Paragraph(f'{woc_header[4]}', detail_value_style)],
        [Paragraph('Nama Vendor', detail_value_style), Paragraph(':', detail_key_style), Paragraph(f'{woc_header[2]}', detail_value_style)],
        [Paragraph('Entity', detail_value_style), Paragraph(':', detail_key_style), Paragraph(f'{woc_header[3]}', detail_value_style)],
        [Paragraph('Keterang Barang / Jasa', detail_value_style), Paragraph(':', detail_key_style), Paragraph(f'{woc_header[5]}', detail_value_style)],
        [Paragraph('Alasan', detail_value_style), Paragraph(':', detail_key_style), Paragraph(f'{woc_header[6]}', detail_value_style)],
    ]

    # PR HEADER TABLE LIST OUTPUT
    table_detail = Table(detail_data, colWidths=[1.8*inch, 0.3*inch, 4.9*inch])
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
    elements.append(Spacer(1, 1))


    # CATATAN:
    descriptions = """1. Sesuai dengan Kebijakan Pembelian, pembelian di atas Rp 1.000.000 harus melalui beberapa vendor RFQ <br/>
                         &nbsp;&nbsp;&nbsp;&nbsp;atau RFP.Jika beberapa vendor tidak tersedia karena alasan-alasan yang diberikan di bawah ini, permintaan <br/>
                         &nbsp;&nbsp;&nbsp;&nbsp;untuk pengabaian formulir tender kompetitif harus menyertai permintaan pembelian.<br/> 
                      2. Dengan menandatangani formulir ini, saya mengkonfirmasi bahwa tidak ada konflik kepentingan yang <br/>
                         &nbsp;&nbsp;&nbsp;&nbsp;diketahui dengan vendor tunggal. <br/>
                      3. Departemen pembelian memiliki keputusan akhir untuk menyetujui atas Waiver of Competition Form."""
    # descriptions = raw_desc.replace("NL", "<br/>")
    detail_data = [
        [Paragraph('', detail_key_style)],
        [Paragraph('Catatan :', detail_value_style)],
        [Paragraph(descriptions, detail_value_style)],
    ]

    # PR HEADER TABLE LIST OUTPUT
    table_detail = Table(detail_data, colWidths=[7*inch])
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
    elements.append(Spacer(1, 1))

    descriptions = """
            1. Vendor Tunggal: <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;Barang atau jasa yang dibutuhkan hanya tersedia dari satu vendor. <br/>
            2. Darurat: <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;Justifikasi pembelian darurat ini hanya diberikan kepada: <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;a. Pencegahan bahaya lingkungan, kesehatan atau keselamatan <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;b. Penyelesaian kebutuhan dengan waktu yang sangat singkat <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;c. Perbaikan darurat dan pemeliharaan peralatan yang ada untuk keperluan sehari hari <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp(misalnya: EDC / TMS) <br/>
            3. Ekonomi : <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;Penggunaan vendor lain akan mengakibatkan ketidaksesuaian dengan kondisi yang ada, <br/>
            &nbsp;&nbsp;&nbsp;&nbsp;membutuhkan pelatihan, waktu dan biaya yang cukup besar; fluktuasi harga yang cepat. <br/>
        """
    detail_data = [
        [Paragraph('', detail_key_style)],
        [Paragraph('Alasan atas permintaan dengan menggunakan Waiver of Competition Bidding :', detail_value_style)],
        [Paragraph(descriptions, detail_value_style)],
    ]

    # PR HEADER TABLE LIST OUTPUT
    table_detail = Table(detail_data, colWidths=[7*inch])
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
    elements.append(Spacer(1, 37))

    ## PR_APPROVAL
    styles = getSampleStyleSheet()
    footer_style.alignment = 1  # Center alignment

    # PR APPROVAL SIGNATURE STRUCTURE
    table_footer_data = [
        [Paragraph('Disetujui oleh:', lefted_style), 
        Paragraph('', footer_style)]
    ]

    # Header row for signature positions
    header_row = [
        Paragraph('Head of Department', footer_style),  # Approval 1
        Paragraph('Head of Finance', footer_style)  # Approval 2
    ]
    table_footer_data.append(header_row)

    for x in range(0):
        table_footer_data.append([Paragraph('', footer_style), Paragraph('', footer_style), Paragraph('', footer_style)])

    # Row untuk tanda tangan dan nama approval
    signature_row = []
    approval_row = []
    date_row = []

    # Tambahkan tanda tangan, tanggal persetujuan, dan nama approval
    for i, approval in enumerate(woc_approval):
        approval_date = str(approval[6]) if approval[6] else ''
        approval_name = f'({approval[3]})' if approval[3] else ''
        sign_path = approval[7] if approval[7] else 'static/uploads/white.png'
        signature_row.append(Image(sign_path, width=50, height=50))
        approval_row.append(Paragraph(approval_name, footer_style))
        date_row.append(Paragraph(f'Tanggal: {approval_date}', date_approval))
        

    # Tambahkan baris ke tabel footer
    table_footer_data.append(signature_row)
    table_footer_data.append(approval_row)
    table_footer_data.append(date_row)

    # Buat tabel footer dengan kolom yang sesuai
    table_footer = Table(table_footer_data, colWidths=[3.4 * inch] * 5)
    table_footer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align content to the top
    ]))

    elements.append(table_footer)
    elements.append(Spacer(1, 12))

    
    # LOGS TRACKER________________________________________________________
    elements.append(PageBreak())
    table_content_style_left_log = ParagraphStyle(name='table_content_left', alignment=TA_CENTER, fontSize=24)
    value_content_style_left_log = ParagraphStyle(name='value_content_style_left_log',  alignment=TA_LEFT, fontSize=10)
    
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

    # Populate the table with woc_logs data
    for index, log in enumerate(woc_logs):
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
            Paragraph(log[2], value_content_style_left_log),
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
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align content to the top
    ]))
    elements.append(logs_table)
    # END LOGS

    # NOT USING MERGE REPORT PDF ONLY_____________________________________
    doc.build(elements)
    doc.setTitle = 'WOC'
    buffer.seek(0)
    return send_file(buffer, as_attachment=False, download_name=f'{no_woc}.pdf', mimetype='application/pdf')
# ====================================================================================================================================
