 # PR APPROVAL SIGNATURE STRUCTURE
    table_footer_data = [
        [Paragraph('Requested by', footer_style), 
        Paragraph('Approved by', footer_style), 
        '', '', '', '']
    ]

    # Tambahkan kolom Head of Department, Head of Finance, dan Direktur di bawah masing-masing kolom yang sesuai
    header_row = [Paragraph('', footer_style),
                Paragraph('Head of Department', footer_style), 
                Paragraph('Head of Finance', footer_style), 
                '',  # Kosong karena kolom Head of Finance span ke kolom ini
                Paragraph('Direktur', footer_style)]

    # Masukkan baris header tambahan ini ke dalam data tabel
    table_footer_data.append(header_row)

    # Menambahkan baris kosong antara nama dan tanda tangan
    for x in range(1):  # Sesuaikan jumlah baris jika diperlukan
        table_footer_data.append([Paragraph('', footer_style)] * 5)

    # Tambahkan tanda tangan dan nama requester
    signature_row = [signature_image]
    date_row = [Paragraph('', date_approval)]
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

    # Tambahkan baris tanda tangan, tanggal, dan nama approval ke dalam tabel footer
    table_footer_data.append(signature_row)
    table_footer_data.append(date_row)
    table_footer_data.append(approval_row)

    # Sesuaikan colWidths agar tabel tidak melebihi lebar halaman
    table_footer = Table(table_footer_data, colWidths=[1.4 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1.4 * inch])
    table_footer.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
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