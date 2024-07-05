# Digital Signature App Documentation

## Introduction : 
####  The Digital Signature App is a web-based application that allows a lender dashboard to upload loan agreements and have multiple borrowers sign these documents digitally. This app provides functionality for viewing, signing, and acknowledging documents.


## Software Tools Used : Python,Django,SQL,HTML,CSS,JavaScript.


## Python/Django Libraries Used:

#### from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
#### from django.http import FileResponse # type: ignore
#### from django.urls import reverse # type: ignore
#### from PyPDF2 import PdfReader, PdfWriter # type: ignore
#### from reportlab.lib.pagesizes import letter # type: ignore
#### from reportlab.pdfgen import canvas # type: ignore
#### from reportlab.lib.utils import ImageReader # type: ignore
#### from django.forms import formset_factory # type: ignore
#### from django.urls import path # type: ignore
#### from django.conf import settings # type: ignore
#### from django.conf.urls.static import static # type: ignore
#### from django.db import models # type: ignore


## Models:

### LoanAgreement:

#### borrower: CharField
#### document: FileField
#### uploaded_at: DateTimeField

### BorrowerSignature:

#### agreement: ForeignKey (LoanAgreement)
#### loan_id: CharField
#### name: CharField
#### mobile_number: IntegerField
#### signature_done: BooleanField 
#### signed_at: DateTimeField
#### signed_document: FileField
#### ip_address: GenericIPAddressField
#### y_position:IntegerField
#### x_position:IntegerField
#### timestamp: DateTimeField

## Forms:

#### NumberOfBorrowersForm : Enters the number of borrowers applied for the loan.
#### BorrowerDetailForm : Enters the details of the borrowers such as Loan ID,Name and Mobile Number
#### LoanAgreementForm : Used for uploading loan agreements.
#### SignatureForm : Used for collecting the borrower signature data.


## Views:

#### LoanProcessView : Allow lenders to enter the number of borrowers,borrower details,upload agreement and generate the links respectively.
#### ViewOriginalDocument : Allow borrowers to view the loan agreement and acknowledge it.
#### SignAgreementView : Opens the signature pad on which the borrower has to sign.
#### SignAgreementSuccessView : Shows the borrower that signature have been done successfully.
#### ViewSignedAgreementView : Show the signed document to the borrower.  



## Adding Signature Functionality:

def add_signature(pdf_path, signature_data_url, loan_id, signature_instance, ip_address, timestamp):
    
    reader = PdfReader(pdf_path)
    
    writer = PdfWriter()
    
    # Decode the base64 image data for the signature

    signature_data = base64.b64decode(signature_data_url.split(',')[1])
    signature_image = Image.open(io.BytesIO(signature_data))
    
    current_date = timezone.now().date().strftime('%Y-%m-%d')
    current_time = timezone.now().time().strftime('%H:%M:%S')

    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        signature_image = signature_image.resize((80, 90))
        
        
        can.drawImage(ImageReader(signature_image), signature_instance.x_position, signature_instance.y_position + 10, width=80, height=90)
        
        text_y_position = signature_instance.y_position + 20
        
        can.drawString(signature_instance.x_position, text_y_position - 10, f"{loan_id}")
        can.drawString(signature_instance.x_position, text_y_position - 20, f"{ip_address}")
        can.drawString(signature_instance.x_position, text_y_position - 30, f"{current_date}")
        can.drawString(signature_instance.x_position, text_y_position - 40, f"{current_time}")
        can.save()

        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]
        page.merge_page(overlay_page)
        writer.add_page(page)

    with open(pdf_path, 'wb') as output_pdf:
        writer.write(output_pdf)

























