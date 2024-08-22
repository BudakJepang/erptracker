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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepInFrame, Frame, PageBreak
from reportlab.graphics.shapes import Drawing, Line
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.colors import Color
# from reportlab.graphics.shapes import Line
from reportlab.pdfgen import canvas
from datetime import datetime
from flask_mysqldb import MySQL, MySQLdb
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
from modules.mail import pr_mail, approval_notification_mail, alert_mail, pr_alert_mail
from modules.logs import insert_pr_log
import socket
import logging

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
prf_blueprint = Blueprint('prf', __name__)
# ====================================================================================================================================


# LIST
@prf_blueprint.route('/prf_list')
@login_required
def prf_list():
    from app import mysql
    return render_template('prf/prf_list.html')

# PRF ADD
@prf_blueprint.route('/prf_add', methods = ['POST', 'GET'])
@login_required
def prf_add():
    prf_number = None
    from app import mysql

    user_entities = session.get('entities', [])

    return render_template('prf/prf_add.html')