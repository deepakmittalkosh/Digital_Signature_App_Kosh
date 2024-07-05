from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, UpdateView, DetailView, FormView
from django.http import HttpResponseBadRequest, HttpResponse, FileResponse
from .forms import LoanAgreementForm, NumberOfBorrowersForm, BorrowerDetailFormSet, BorrowerDetailForm
from .models import BorrowerSignature, LoanAgreement
from django.forms import formset_factory
from django.utils import timezone
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
import base64
from PIL import Image
import datetime

class LoanProcessView(View):
    def get(self, request, *args, **kwargs):
        step = request.GET.get('step', 'number_of_borrowers')
        
        if step == 'borrower_details':
            num_borrowers = int(request.GET.get('num_borrowers'))
            BorrowerDetailFormSet = formset_factory(BorrowerDetailForm, extra=num_borrowers)
            formset = BorrowerDetailFormSet()
            return render(request, 'loan_process.html', {'step': step, 'formset': formset, 'num_borrowers': num_borrowers})
        
        elif step == 'upload_agreement':
            agreement_id = request.GET.get('agreement_id')
            upload_form = LoanAgreementForm()
            return render(request, 'loan_process.html', {'step': step, 'upload_form': upload_form, 'agreement_id': agreement_id})
        
        elif step == 'generate_links':
            agreement_id = request.GET.get('agreement_id')
            agreement = get_object_or_404(LoanAgreement, pk=agreement_id)
            borrowers = BorrowerSignature.objects.filter(agreement=agreement)
            # Assuming you want to generate unique links based on some criteria (e.g., Django's reverse mechanism)
            borrower_links = {borrower.name: request.build_absolute_uri(reverse('view_original_document', args=[agreement.id, borrower.id])) for borrower in borrowers}
            return render(request, 'loan_process.html', {'step': step, 'agreement': agreement, 'borrower_links': borrower_links})
        
        else:  # Default step: number_of_borrowers
            number_form = NumberOfBorrowersForm()
            return render(request, 'loan_process.html', {'step': 'number_of_borrowers', 'number_form': number_form})

    def post(self, request, *args, **kwargs):
        step = request.POST.get('step')
        
        if step == 'number_of_borrowers':
            number_form = NumberOfBorrowersForm(request.POST)
            if number_form.is_valid():
                num_borrowers = number_form.cleaned_data['num_borrowers']
                return redirect(reverse('loan_process') + f'?step=borrower_details&num_borrowers={num_borrowers}')
        
        elif step == 'borrower_details':
            num_borrowers = int(request.POST.get('num_borrowers'))
            BorrowerDetailFormSet = formset_factory(BorrowerDetailForm, extra=num_borrowers)
            formset = BorrowerDetailFormSet(request.POST)
            if formset.is_valid():
                agreement = LoanAgreement.objects.create() # Create a new LoanAgreement instance
                for form in formset:
                    loan_id = form.cleaned_data['loan_id']
                    name = form.cleaned_data['name']
                    mobile_number = form.cleaned_data['mobile_number']
                    BorrowerSignature.objects.create(
                        agreement=agreement,
                        loan_id=loan_id,
                        name=name,
                        mobile_number=mobile_number
                    )
                return redirect(reverse('loan_process') + f'?step=upload_agreement&agreement_id={agreement.id}')
        
        elif step == 'upload_agreement':
            agreement_id = request.POST.get('agreement_id')
            upload_form = LoanAgreementForm(request.POST, request.FILES)
            if upload_form.is_valid():
                agreement = get_object_or_404(LoanAgreement, pk=agreement_id)
                agreement.document = upload_form.cleaned_data['document']
                agreement.save()
                return redirect(reverse('loan_process') + f'?step=generate_links&agreement_id={agreement_id}')
        
        return redirect('loan_process')


class ViewOriginalDocumentView(View):
    def get(self, request, agreement_id, borrower_id):
        agreement = get_object_or_404(LoanAgreement, pk=agreement_id)
        borrower = get_object_or_404(BorrowerSignature, pk=borrower_id, agreement=agreement)
        context = {
            'document_url': agreement.document.url,
            'borrower': borrower,
        }
        return render(request, 'original_document.html', context)
    
    def post(self, request, agreement_id, borrower_id):
        if request.POST.get('acknowledge_checkbox'):# Check if the user has acknowledged the document
            return redirect('sign_agreement', agreement_id=agreement_id, borrower_id=borrower_id)
        else:
            return HttpResponseBadRequest("Please acknowledge the document.")


class SignAgreementView(View):
    def get(self, request, agreement_id, borrower_id):
        agreement = get_object_or_404(LoanAgreement, pk=agreement_id)
        borrower = get_object_or_404(BorrowerSignature, pk=borrower_id, agreement=agreement)
        #Check if the borrower already_signed the loan_agreement
        existing_signature = BorrowerSignature.objects.filter(agreement=agreement, signature_done = True,name =borrower.name).exists()
        if existing_signature:
            return render(request, 'already_signed.html', {'agreement': agreement})
        context = {
            'agreement': agreement,
            'borrower': borrower,
        }
        return render(request, 'sign_agreement.html', context)
    
    def post(self, request, agreement_id, borrower_id):
        agreement = get_object_or_404(LoanAgreement, pk=agreement_id)
        borrower = get_object_or_404(BorrowerSignature, pk=borrower_id, agreement=agreement)
       
        
        signature_data_url = request.POST.get('signature')
        if signature_data_url:
            signatures = BorrowerSignature.objects.filter(agreement=agreement, signature_done=True).count()
            signatures_per_row = 5  # Number of signatures per row
            horizontal_spacing = 120  # Spacing between signatures horizontally
            vertical_spacing = 120  # Spacing between signatures vertically
            x_offset = 25  # Initial x offset
            y_offset = 25  # Initial y offset
        
            # Calculate position for the new signature
            x_position = x_offset + (signatures % signatures_per_row) * horizontal_spacing  # Adjust horizontal spacing
            y_position = y_offset + (signatures // signatures_per_row) * vertical_spacing  # Adjust vertical spacing
        
            # Update the existing BorrowerSignature instance
            BorrowerSignature.objects.filter(agreement=agreement, name=borrower.name).update(
                signature_done=True,
                x_position=x_position,
                y_position=y_position,
                ip_address=request.META.get('REMOTE_ADDR'),
                timestamp=timezone.now(),
            )
            # Fetch the updated signature instance
            signature_instance = BorrowerSignature.objects.get(agreement=agreement, name=borrower.name)
            signature_instance.save()
            ip_address = request.META.get('REMOTE_ADDR')
            timestamp = timezone.now()

            add_signature(agreement.document.path, signature_data_url, borrower.loan_id, signature_instance, ip_address, timestamp)
            
            return redirect('sign_agreement_success', agreement_id=agreement_id, borrower_id=borrower_id)


class SignAgreementSuccessView(View):
    def get(self, request, agreement_id, borrower_id):
        agreement = get_object_or_404(LoanAgreement, pk=agreement_id)
        borrower = get_object_or_404(BorrowerSignature, pk=borrower_id, agreement=agreement)
        return render(request, 'sign_agreement_success.html', {'agreement': agreement, 'borrower': borrower})


class ViewSignedAgreementView(View):
    def get(self, request, agreement_id, borrower_id):
        agreement = get_object_or_404(LoanAgreement, pk=agreement_id)
        return FileResponse(agreement.document.open(), content_type='application/pdf')


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
