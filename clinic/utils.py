from django.conf import settings
from django.core.mail import send_mail


def test_send(subject, message, recipients):
	send_mail(
    		subject=subject,
    		message=message,
    		from_email=settings.DEFAULT_FROM_EMAIL,
    		recipient_list=recipients)

def send_email(subject, message, recipients):
	send_mail(
    		subject=subject,
    		message='',
    		from_email=settings.DEFAULT_FROM_EMAIL,
    		recipient_list=recipients,
			html_message=message
			)

def contact_us(message, sender):
	send_mail(
    		subject="Contact Us",
    		message=message,
    		from_email=sender,
    		recipient_list=list(settings.EMAIL_HOST_USER))


def send_results_ready_email(patient_email, patient_name, appointment_date):
    # Subject of the email
    subject = 'Your Medical Results are Ready for Pick-up'
    
    # Message body
    message = f"""
    Dear {patient_name},

    We hope this message finds you well. We are pleased to inform you that the results for your medical appointment on {appointment_date} are ready for pick-up.

    You can collect your results from our clinic during our regular business hours. Should you have any questions or need further assistance, please do not hesitate to contact us.

    Thank you for choosing our clinic for your healthcare needs. We look forward to assisting you again.

    Best regards,
    AsherMD Clinic
    """

    # Sender's email (configured in Django settings)
    from_email = settings.DEFAULT_FROM_EMAIL

    # Send the email
    send_mail(
        subject,          # Subject
        message,          # Message
        from_email,       # From
        [patient_email],  # To
        fail_silently=False
    )