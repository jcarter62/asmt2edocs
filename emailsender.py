import os
import smtplib
from asyncio import timeout
from email.message import EmailMessage
from dotenv import load_dotenv
from datetime import datetime
import requests

class EmailSender:

    def __init__(self):
        load_dotenv()

        self.method = os.getenv('SEND_METHOD', 'smtp').lower()

        self.mail_from = os.getenv('MAIL_FROM')
        self.mail_from_name = os.getenv('MAIL_FROM_NAME', '')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.example.com')  # Add SMTP server
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))  # Add SMTP port
        self.smtp_user = os.getenv('SMTP_USER', '')  # Add SMTP username
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')  # Add SMTP password
        #
        self.debug = False
        self.debug_recipients = []
        # determine if test_flag is set, and test_email is set.
        self.test_flag = (os.getenv('TEST_FLAG', 'off').lower() == 'on')
        self.test_email = os.getenv('TEST_EMAIL', '').strip()
        if self.test_email > '':
            if self.test_flag:
                self.debug = True
                self.debug_recipients = [self.test_email]

        # self.debug = (os.getenv('MAIL_DEBUG', 'False') == 'True')
        # self.debug_recipients = [os.getenv('MAIL_DEBUG_TO_ADDRESS', '')]
        self.debug_prefix = '[EmailSender] '

        self.api = os.getenv('SMTP2GO_API_KEY', '')

        self.smtp_connection = None
        if self.method == 'smtp':
            self.dbg_msg('0a')
            self.smtp_connection = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.dbg_msg('0b')

        return

    def __del__(self):
        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
            except Exception as e:
                print(f'Error closing SMTP connection: {e}')
            self.smtp_connection = None

    def logmsg(self, msg):
        if self.debug:
            print(f'{self.debug_prefix}:{msg}')

    def create_message(self, subject, recipients, plain_body='', html_body='', attachments=None):
        self.logmsg(f'Creating email message with subject: {subject}')
        self.subject = subject
        self.recipients = recipients
        self.plain_body = plain_body
        self.html_body = html_body
        self.attachments = attachments or []
        if self.debug:
            self.recipients = self.debug_recipients
            self.logmsg(f'Updated Recipients: {self.recipients}')
        return

    def dbg_msg(self, msg):
        """Debug message for email sender."""
        if self.debug:
            print(f'{self.debug_prefix} {msg} {datetime.now()}')


    def send_email(self):

        if self.method == 'smtp':
            try:
                self.logmsg('Preparing to send email message.')
                msg = EmailMessage()
                msg['From'] = f"{self.mail_from_name} <{self.mail_from}>"
                msg['To'] = ', '.join(self.recipients)
                msg['Subject'] = self.subject
                msg.set_content(self.plain_body)

                # Add HTML content if provided
                if self.html_body:
                    msg.add_alternative(self.html_body, subtype='html')


                # Add attachments if provided
                for attachment in self.attachments:
                    with open(attachment, 'rb') as f:
                        file_data = f.read()
                        file_name = os.path.basename(attachment)
                        msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)

                # Connect to SMTP server and send email
                with self.smtp_connection as server:
                    server.starttls()  # Upgrade the connection to secure
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

                self.logmsg('Email message sent successfully.')
            except Exception as e:
                self.logmsg(f'Error sending email: {e}')
                raise RuntimeError(f"Failed to send email: {e}")
        else: # send via api.
            try:
                url = 'https://api.smtp2go.com/v3/email/send'

                payload = {
                    'to': self.recipients,
                    'sender': f"{self.mail_from_name} <{self.mail_from}>",
                    'subject': self.subject,
                    'text_body': self.plain_body,
                    'html_body': self.html_body,
                }

                headers = {
                    'accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-Smtp2go-Api-Key': self.api
                }

                response = requests.post(url, json=payload, headers=headers)

                self.logmsg('Email message sent successfully.' + response.text)
            except Exception as e:
                self.logmsg(f'Error sending email via API: {e}')
                raise RuntimeError(f"Failed to send email via API: {e}")

