from django.test import TestCase
from django.core.mail import send_mail
from django.conf import settings

class EmailTests(TestCase):
    def test_send_email(self):
        print("⚙️ Attempting to send email...")  # Debug statement

        result = send_mail(
            subject='SMTP Test',
            message='If you see this, SMTP works.',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['tallibneemah@gmail.com'],  # Replace with your real email
            fail_silently=False
        )

        if result == 1:
            print("✅ Email was sent successfully.")
        else:
            print("❌ Email was NOT sent.")

        self.assertEqual(result, 1)



'''
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    subject='SMTP Test',
    message='If you see this, SMTP works.',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['tallibneemah@gmail.com'],  # Use your real email
    fail_silently=False
)
youtube comments nd vid
snap login
the boys
'''
