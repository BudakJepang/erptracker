# MAIN PR SUBMIT 
@pr_blueprint.route('/pr_temp_submit', methods=['GET', 'POST'])
def pr_temp_submit():
    pr_number = None
    from app import mysql
    
    # get the user entities and departments from session
    user_entities = session.get('entities', [])
    user_departments = session.get('departments', [])
    
    # convert entities and departments to a list of IDs for filtering query
    entity_ids = [entity['entity_id'] for entity in user_entities]
    department_ids = [dept['department_id'] for dept in user_departments]

    cursor = mysql.connection.cursor()
    
     # entities accessible by the user (implement filtered entity id here from session above)
    if entity_ids:
        cursor.execute("SELECT id, entity, entity_name FROM entity WHERE id IN %s", (tuple(entity_ids),))
        entities = cursor.fetchall()
    else:
        entities = []

    # departments accessible by the user (implement filtered department id here from session above)
    if department_ids:
        cursor.execute("SELECT id, entity_id, department, department_name FROM department WHERE id IN %s", (tuple(department_ids),))
        departments = cursor.fetchall()
    else:
        departments = []

    cursor.execute("SELECT id, username, email FROM user_accounts WHERE level = 4")
    approver = cursor.fetchall()

    if request.method == 'POST':
        # Variable PR Header
        entity = request.form['entity']
        department = request.form['department']
        no_pr = generate_pr_number(entity, department)
        tanggal_permintaan = request.form['tanggal_permintaan']
        requester_name = session.get('username', 'system')
        requester_id = session.get('id', 'system')
        total_budget_approved = request.form['total_budget_approved']
        nama_project = request.form['nama_project']
        remarks = None

        # Get approval values from form PR_HEADER
        approval1_user_id = request.form.get('approval1_user_id', None)
        approval2_user_id = request.form.get('approval2_user_id', None)
        approval3_user_id = request.form.get('approval3_user_id', None)

        approval1_user_id = approval1_user_id if approval1_user_id else None
        approval2_user_id = approval2_user_id if approval2_user_id else None
        approval3_user_id = approval3_user_id if approval3_user_id else None
        approval1_status = None
        approval1_notes = None
        approval2_status = None
        approval2_notes = None
        approval3_status = None
        approval3_notes = None

        # Variable for AUTO_NUM table
        current_date = datetime.now()
        year_month = current_date.strftime('%y%m')

        # Insert into pr_autonum
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

        # Insert into pr_header
        if entity == 'OID':
            entity = 2
        elif entity == 'CNI':
            entity = 1
        insert_header_query = '''
            INSERT INTO pr_header (no_pr, tanggal_permintaan, requester_id, requester_name, nama_project, entity_id, total_budget_approved, remarks, approval1_status,
                                   approval1_user_id, approval1_notes, approval2_status, approval2_user_id, approval2_notes, approval3_status, approval3_user_id,
                                   approval3_notes, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(insert_header_query, (no_pr, tanggal_permintaan, requester_id, requester_name, nama_project, entity, total_budget_approved, remarks, approval1_status,
                                             approval1_user_id, approval1_notes, approval2_status, approval2_user_id, approval2_notes, approval3_status, approval3_user_id, approval3_notes, today, today))
        mysql.connection.commit()

        # Provisioning insert into pr_detail
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
        pr_mail(no_pr, entity, department, nama_project, tanggal_permintaan, total_budget_approved, tanggal, approval2_user_id)
        flash('New PR has been added', 'success')

        return redirect(url_for('pr.pr_list'))
    return render_template('pr/pr_temp.html', pr_number=pr_number, entities=entities, departments=departments, approver=approver)
# ==========================================================================================================================================

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
        
        if approval_user_id == 1:  
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

# HTML
# PR DETAIL 
{% extends 'base.html' %}

<!-- INHERETENCE SIDEBAR -->

<!--END INHERETENCE SIDEBAR -->

<!-- INHERETENCE CONTENT -->
{% block content %}

<style>
    .status-pending {
        color: orange;
        font-weight: bold;
    }
    .status-approved {
        color: green;
    }
    .status-rejected {
        color: red;
    }
</style>
<!-- MAIN CONTENT -->

<!-- Content Wrapper. Contains page content -->
<div class="content-wrapper">
    <!-- Content Header (Page header) -->
    <section class="content-header">
      <div class="container-fluid">
        <div class="row mb-2">
          <div class="col-sm-6">
            <h1>PR DETAIL</h1>
          </div>
          <div class="col-sm-6">
            <ol class="breadcrumb float-sm-right">
              <li class="breadcrumb-item"><a href="#">Home</a></li>
              <li class="breadcrumb-item active">Invoice</li>
            </ol>
          </div>
        </div>
      </div><!-- /.container-fluid -->
    </section>

<!-- Main FORM -->
<section class="content">
    <div class="container-fluid">
      <div class="row">
        <div class="col-md-12">
          <!-- Main content -->
          <div class="invoice p-3 mb-3">
            <!-- title row -->
            <div class="row" style="padding-top: 30px;">
              <div class="col-12">
                <h4>
                  <img src="{{ url_for('static', filename='entity_logo/unnamed.png') }}" height="60" width="60"> Purchase Requisition, (PR).
                  <small class="float-right">{{ data[0][27] }}</small>
                </h4>
              </div>
            </div>
            <!-- info row -->
            <div class="row invoice-info" style="padding-top: 10px;">
              <div class="col-sm-12 invoice-col">
                <address>
                  <strong style="font-size: 18px;">PR Number : {{ data[0][0]}}</strong><br>
                  <hr>
                  <table class="" style="width:100%; border-spacing: 0;">
                    <tr>
                      <td style="text-align: left; width: 15%; padding-top: 10px;">Request Date</td>
                      <td style="text-align: left; width: 1%;">:</td>
                      <td style="text-align: left; width: 65%;">{{ data[0][1] }}</td>  
                    </tr>
                    <tr>
                      <td style="text-align: left; width: 15%;">User / Requester</td>
                      <td style="text-align: left; width: 1%;">:</td>
                      <td style="text-align: left; width: 65%;">{{ data[0][3] }}</td>  
                    </tr>
                    <tr>
                      <td style="text-align: left; width: 15%;">Project Name</td>
                      <td style="text-align: left; width: 1%;">:</td>
                      <td style="text-align: left; width: 65%;">{{ data[0][4] }}</td>  
                    </tr>
                    <tr>
                      <td style="text-align: left; width: 15%;">Budget Source / Entity</td>
                      <td style="text-align: left; width: 1%;">:</td>
                      <td style="text-align: left; width: 65%;">{{ data[0][26] }}</td>  
                    </tr>
                    <tr>
                      <td style="text-align: left; padding-top: 20px; width: 15%;"><strong style="font-size: 18px;">Total Budget Approved</strong></td>
                      <td style="text-align: left; padding-top: 20px; width: 1%;">:</td>
                      <td style="text-align: left; padding-top: 20px; width: 65%;"><strong style="font-size: 18px;">Rp. {{ "{:,.0f}".format(data[0][6]) }}</strong></td>  
                    </tr>
                  </table>
                </address>
              </div>
            </div>
            <hr>
            <div class="row">
              <div class="col-md-12">
                <table class="table table-bordered">
                  <thead>
                    <tr style="text-align: center;">
                      <th>No</th>
                      <th>Nama Barang / Jasa</th>
                      <th>Spesifikasi Barang/Jasa</th>
                      <th>QTY</th>
                      <th>Tanggal Dibutuhkan</th>
                    </tr>
                  </thead>
                  <tbody>
                    {% for row in data %}
                    <tr>
                      <td style="text-align: center;">{{ row[20]}}</td>
                      <td>{{ row[21] }}</td>  
                      <td>{{ row[22] }}</td>  
                      <td>{{ row[23] }}</td>  
                      <td>{{ row[24] }}</td>  
                    </tr>
                    {% endfor %}
                  </tbody>
                </table>
                <hr>
              </div>
            </div>
  
            <div class="row">
              <div class="col-md-6">
                <p class="lead">Remarks:</p>
                <hr>
                <p class="text-muted well well-sm shadow-none" style="margin-top: 10px; padding-left: 30px;">
                  <i class="fa fa-check" aria-hidden="true"></i> Lampirkan gambar jika ada.
                </p>
                <p class="text-muted well well-sm shadow-none" style="margin-top: 10px; padding-left: 30px;">
                  <i class="fa fa-check" aria-hidden="true"></i> Urgent / Penunjukan vendor langsung harus melampirkan form walver.
                </p>
              </div>
              <div class="col-md-6">
                <p class="lead">Documents:</p>
                <hr>
                <table class="table table-bordered" id="approval-table">
                  <thead>
                    <tr>
                      <th style="width: 10px">No</th>
                      <th style="text-align: center;">File Name</th>
                      <th style="width: 90px; text-align: center;">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style="width: 1%">1.</td>
                      <td style="width: 50%">
                        <p>{{ data[0][25] }}</p>
                      </td>
                      <td style="text-align: center;">
                        <link rel="image_src" href="image url" />
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <hr>
            <!-- /.col -->

            <div class="row invoice-info" style="padding-top: 10px;">
                <div class="col-sm-6 invoice-col">
                  <address>
                    <table class="" style="width:100%; border-spacing: 0;">
                      <tr>
                        <td style="text-align: left; width: 15%; padding-top: 10px;  padding-bottom: 10px">Dibuat Oleh</td>
                        <td style="text-align: left; width: 1%; padding-top: 10px;  padding-bottom: 10px">:</td>
                        <td style="text-align: left; width: 65%; font-weight: bold; padding-top: 10px; padding-bottom: 10px">{{ data[0][3] }}</td>  
                      </tr>
                        {% if current_user_id == data[0][9] %}
                        <tr>
                          <td style="text-align: left; width: 15%; padding-top: 10px;">Disetujui Oleh</td>
                          <td style="text-align: left; width: 1%; padding-top: 10px;">:</td>
                          <td style="text-align: left; width: 65%; font-weight: bold; padding-top: 10px;">{{ data[0][11] }}</td>  
                        </tr>
                        <tr>
                            <td style="text-align: left; width: 15%; padding-top: 10px;">Status Persetujuan</td>
                            <td style="text-align: left; width: 1%; padding-top: 10px;">:</td>
                            <td style="text-align: left; width: 65%; font-weight: bold; padding-top: 10px;">
                                {% if data[0][8] is none %}
                                    <span class="badge badge-warning">PENDING</span>
                                {% elif data[0][8] == 'APPROVED' %}
                                    <span class="badge badge-success">APPROVED</span>
                                {% elif data[0][8] == 'REJECTED' %}
                                    <span class="badge badge-danger">REJECTED</span>
                                {% else %}
                                    {{ data[0][8] }}
                                {% endif %}
                            </td>
                        </tr>
                        <tr>
                          <td style="text-align: left; width: 15%; padding-top: 10px; padding-top: 10px;">Action</td>
                          <td style="text-align: left; width: 1%; padding-top: 10px;">:</td>
                          <td style="padding-top: 10px;">
                            <button type="button" class="btn btn-success btn-sm" title="Approve PR" data-toggle="modal" data-target="#modal-approve" data-id="">
                                <i class="fa fa-check" aria-hidden="true"></i> APPROVED
                            </button>
                            <button type="button" class="btn btn-danger btn-sm" title="Approve PR" data-toggle="modal" data-target="#modal-reject" data-id="">
                                <i class="fa fa-times" aria-hidden="true"></i> REJECT
                            </button>
                          </td>
                        </tr>
                        {% elif current_user_id == data[0][13] and data[0][8] == 'APPROVED' %}
                        <tr>
                          <td style="text-align: left; width: 15%; padding-top: 10px;">Disetujui Oleh</td>
                          <td style="text-align: left; width: 1%; padding-top: 10px;">:</td>
                          <td style="text-align: left; width: 65%; font-weight: bold; padding-top: 10px;">{{ data[0][15] }}</td>  
                        </tr>
                        <tr>
                            <td style="text-align: left; width: 15%; padding-top: 10px;">Status Persetujuan</td>
                            <td style="text-align: left; width: 1%; padding-top: 10px;">:</td>
                            <td style="text-align: left; width: 65%; font-weight: bold; padding-top: 10px;">
                                {% if data[0][12] is none %}
                                    <span class="badge badge-warning">PENDING</span>
                                {% elif data[0][12] == 'APPROVED' %}
                                    <span class="badge badge-success">APPROVED</span>
                                {% elif data[0][12] == 'REJECTED' %}
                                    <span class="badge badge-danger">REJECTED</span>
                                {% else %}
                                    {{ data[0][12] }}
                                {% endif %}
                            </td>
                        </tr>
                        <tr>
                          <td style="text-align: left; width: 15%; padding-top: 10px; padding-top: 10px;">Action</td>
                          <td style="text-align: left; width: 1%; padding-top: 10px;">:</td>
                          <td style="padding-top: 10px;">
                            <button type="button" class="btn btn-success btn-sm" title="Approve PR" data-toggle="modal" data-target="#modal-approve" data-id="">
                                <i class="fa fa-check" aria-hidden="true"></i> APPROVED
                            </button>
                            <button type="button" class="btn btn-danger btn-sm" title="Approve PR" data-toggle="modal" data-target="#modal-reject" data-id="">
                                <i class="fa fa-times" aria-hidden="true"></i> REJECT
                            </button>
                          </td>
                        </tr>
                        {% elif current_user_id == data[0][17] and data[0][13] == 'APPROVED' %}
                        <tr>
                          <td style="text-align: left; width: 15%; padding-top: 10px;">Disetujui Oleh</td>
                          <td style="text-align: left; width: 1%; padding-top: 10px;">:</td>
                          <td style="text-align: left; width: 65%; font-weight: bold; padding-top: 10px;">{{ data[0][19] }}</td>  
                        </tr>
                        <tr>
                            <td style="text-align: left; width: 15%; padding-top: 10px;">Status Persetujuan</td>
                            <td style="text-align: left; width: 1%; padding-top: 10px;">:</td>
                            <td style="text-align: left; width: 65%; font-weight: bold; padding-top: 10px;">
                                {% if data[0][16] is none %}
                                    <span class="badge badge-warning">PENDING</span>
                                {% elif data[0][16] == 'APPROVED' %}
                                    <span class="badge badge-success">APPROVED</span>
                                {% elif data[0][16] == 'REJECTED' %}
                                    <span class="badge badge-danger">REJECTED</span>
                                {% else %}
                                    {{ data[0][16] }}
                                {% endif %}
                            </td>
                        </tr>
                        <tr>
                          <td style="text-align: left; width: 15%; padding-top: 10px; padding-top: 10px;">Action</td>
                          <td style="text-align: left; width: 1%; padding-top: 10px;">:</td>
                          <td style="padding-top: 10px;">
                            <button type="button" class="btn btn-success btn-sm" title="Approve PR" data-toggle="modal" data-target="#modal-approve" data-id="">
                                <i class="fa fa-check" aria-hidden="true"></i> APPROVED
                            </button>
                            <button type="button" class="btn btn-danger btn-sm" title="Approve PR" data-toggle="modal" data-target="#modal-reject" data-id="">
                                <i class="fa fa-times" aria-hidden="true"></i> REJECT
                            </button>
                          </td>
                        </tr>
                        {% else %}
                        <table class="table table-striped">
                            <thead>
                              <tr style="text-align: left;">
                                <th>Approver</th>
                                <th>Status</th>
                                <th>Action</th>
                              </tr>
                            </thead>
                            <tbody>
                                {% set approvals = [
                                    {'username': data[0][11], 'status': data[0][8]},
                                    {'username': data[0][15], 'status': data[0][12]},
                                    {'username': data[0][19], 'status': data[0][16]}
                                ] %}
                                {% for approval in approvals %}
                                    {% if approval.username is not none %}
                                        <tr>
                                            <td>{{ approval.username }}</td>
                                            <td style="text-align: left; width: 65%; font-weight: bold;">
                                                {% if approval.status is none %}
                                                    <span class="badge badge-warning">PENDING</span>
                                                {% elif approval.status == 'APPROVED' %}
                                                    <span class="badge badge-success">APPROVED</span>
                                                {% elif approval.status == 'REJECTED' %}
                                                    <span class="badge badge-danger">REJECTED</span>
                                                {% else %}
                                                    {{ approval.status }}
                                                {% endif %}
                                            </td>
                                            <td style="text-align: left; width: 65%; font-weight: bold;">
                                                <a href="{{ url_for('pr.pr_temp_submit') }}" class="btn btn-app bg-default" title="add pr">
                                                    <i class="fa fa-envelope" aria-hidden="true"></i> Send Mail
                                                </a>
                                            </td>
                                        </tr>
                                    {% endif %}
                                {% endfor %}
                            </tbody>
                          </table>
                        {% endif %}
                    </table>
                  </address>
                </div>
            </div>
            <hr>
          <!-- /.col -->
          <!-- this row will not appear when printing -->
          <div class="row no-print" style="padding-top: 50px; padding-bottom: 50px">
            <div class="col-12">
              <!-- <a href="invoice-print.html" rel="noopener" target="_blank" class="btn btn-default"><i class="fas fa-print"></i> Print</a> -->
              <a href="{{ url_for('pr.pr_list') }}" class="btn btn-default float-right" title="Detail">Back to list</a>
              <button type="button" class="btn btn-danger float-right" style="margin-right: 5px;">
                  <i class="fa fa-file-pdf" aria-hidden="true"></i> Generate PDF
              </button>
            </div>
          </div>
        </div>
        <!-- /.invoice -->
      </div><!-- /.col -->
    </div><!-- /.row -->
  </div><!-- /.container-fluid -->
</section>
<!-- /.content -->

<!-- APPROVE MODAL -->
<div class="modal fade" id="modal-approve">
    <div class="modal-dialog">
      <div class="modal-content bg-success">
        <div class="modal-header">
          <h4 class="modal-title">You will approve this PR</h4>
          <button type="button" class="close" data-dismiss="modal" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <form action="{{ url_for('pr.pr_approved', no_pr=data[0][0]) }}" method="POST">
        <div class="modal-body">
          <div class="form-group">
            <label for="exampleInputEmail1">Reason Approved</label>
            <textarea class="form-control" rows="3" id="spesifikasi1" name="spesifikasi1" placeholder="Enter ..." required></textarea>
          </div>
            <div class="form-group">
            <div id="menu-checkboxes">
              </div>
            </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
          <button type="submit" class="btn btn-default">Save</button>
        </div>
      </form>
      </div>
      <!-- /.modal-content -->
    </div>
  </div>
  <!--END APPROVE MODAL -->

<!-- APPROVE MODAL -->
<div class="modal fade" id="modal-reject">
    <div class="modal-dialog">
      <div class="modal-content bg-danger">
        <div class="modal-header">
          <h4 class="modal-title">You will Reject this PR</h4>
          <button type="button" class="close" data-dismiss="modal" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <form action="{{ url_for('user.register') }}" method="POST">
        <div class="modal-body">
          <div class="form-group">
            <label for="exampleInputEmail1">Reason Rejected</label>
            <textarea class="form-control" rows="3" id="spesifikasi1" name="spesifikasi1" placeholder="Enter ..." required></textarea>
          </div>
            <div class="form-group">
            <div id="menu-checkboxes">
              </div>
            </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
          <button type="submit" class="btn btn-default">Save</button>
        </div>
      </form>
      </div>
      <!-- /.modal-content -->
    </div>
  </div>
  <!--END APPROVE MODAL -->



{% endblock %}
<!-- END INHERETENCE CONTENT -->