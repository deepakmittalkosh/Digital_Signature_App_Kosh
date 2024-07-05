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

### LoanAgreement
#### borrower: CharField
#### document: FileField
#### uploaded_at: DateTimeField

### BorrowerSignature
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

## Forms
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
def add_signature(pdf_path, signature_data_url, loan_id, signature_instance):
   reader = PdfReader(pdf_path)
   writer = PdfWriter()


   # Decode the base64 image data for the signature
   signature_data = base64.b64decode(signature_data_url.split(',')[1])
   signature_image = Image.open(io.BytesIO(signature_data))


   for page_num in range(len(reader.pages)):
       page = reader.pages[page_num]
       packet = io.BytesIO()
       can = canvas.Canvas(packet, pagesize=letter)
      
       box_x = signature_instance.x_position - 5
       box_y = signature_instance.y_position - 12
       box_width = 100  # Adjust width as needed
       box_height = 90  # Adjust height as needed
       can.rect(box_x, box_y, box_width, box_height, stroke=1, fill=0)


       # Position the signature at the calculated position
       width, height = letter
       signature_image = signature_image.resize((75, 75))
       can.drawImage(ImageReader(signature_image), signature_instance.x_position, signature_instance.y_position, width=75, height=75)
       #can.drawString(signature_instance.x_position, signature_instance.y_position + 110, f"Loan ID: {loan_id}")
       text_y_position = signature_instance.y_position - 10  # Adjust this value to position below
       can.drawString(signature_instance.x_position, text_y_position, f"Loan ID: {loan_id}")


       can.save()


       packet.seek(0)
       overlay_pdf = PdfReader(packet)
       overlay_page = overlay_pdf.pages[0]


       # Merge the overlay page with the original page
       page.merge_page(overlay_page)
       writer.add_page(page)


   with open(pdf_path, 'wb') as output_pdf:
       writer.write(output_pdf)

























