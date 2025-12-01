import smtplib
import mimetypes
from email.message import EmailMessage
from email.utils import formataddr
from datetime import datetime
from datetime import timezone
import logging
import os

from email.utils import parseaddr


def send_error_email(run_id, flow_name, error_details):
    subject = f"Flow Error Alert - {flow_name} (Run ID: {run_id})"
    body = f"""\
An error occurred in flow '{flow_name}' (Run ID: {run_id}).

Error details:
{error_details}

Timestamp: {datetime.now(timezone.utc).isoformat()}

Please check the logs and Firestore audit collection for more details.
"""
    sender_email = "ADD YOUR SENDER EMAIL"
    sender_name = "Flow Alert"
    password = os.environ.get("EMAIL_PASSWORD")
    if not password:
        logging.error("EMAIL_PASSWORD environment variable is not set!")

    receiver_email = "ADD YOUR RECEIVER EMAIL"
    try:
        success = send_email(
            subject=subject,
            body=body,
            sender_email=sender_email,
            sender_name=sender_name,
            sender_password=password,
            recipient_email=receiver_email,
            recipient_cc=None,
            recipient_bcc=None,
            reply_to=None,
            attachment_bytes=None,
            attachment_filename=None,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
        )
        if not success:
            logging.error(
                f"❌ Failed to send error notification email for run {run_id}"
            )
        else:
            logging.info(f"✅ Sent error notification email for run {run_id}")
    except Exception as ex:
        logging.error(
            f"❌ Exception occurred while sending error email for run {run_id}: {ex}",
            exc_info=True,
        )


# ***********************************************************************************
# Helper function to send emails - ADVANCED VERSION
# Supports different sender login and visible sender
# Supports HTML content and attachments
# Supports DSN (Delivery Status Notification)
# Makes sure that the mailbox always uses pure email addresses (no names) (to avoid autofill issues)
# ***********************************************************************************


def normalize_address(addr: str) -> str:
    """
    Ensures that Gmail cannot use old autocomplete contacts.
    Returns only the pure email address.
    """
    _, email_only = parseaddr(addr)
    return email_only or addr


def normalize_recipient_field(value):
    """
    Safely normalize To/CC/BCC input.
    Handles:
        - None
        - single string
        - list of strings
    """
    if not value:
        return []

    if isinstance(value, list):
        return [normalize_address(str(v)) for v in value]

    return [normalize_address(str(value))]


def send_email(
    subject,
    body,
    from_email,
    from_name,
    smtp_user,
    smtp_password,
    recipient_email,
    recipient_cc=None,
    recipient_bcc=None,
    reply_to=None,
    attachment_bytes=None,
    attachment_filename=None,
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    html_content=False,
    request_dsn=False,
):
    print("HELPER: Preparing to send email...")
    print(f"Subject: {subject}")
    print(f"From: {from_name} <{from_email}>")
    print(f"To: {recipient_email}")
    print(f"CC: {recipient_cc}")
    print(f"BCC: {recipient_bcc}")

    msg = EmailMessage()
    msg["Subject"] = subject

    # Visible sender
    msg["From"] = f"{from_name} <{from_email}>"
    msg["Sender"] = smtp_user  # prevents Gmail from rewriting

    # --- SAFE NORMALIZATION ---
    to_list = normalize_recipient_field(recipient_email)
    cc_list = normalize_recipient_field(recipient_cc)
    bcc_list = normalize_recipient_field(recipient_bcc)

    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    if reply_to:
        msg["Reply-To"] = reply_to

    # HTML or text
    if html_content:
        msg.set_content("This email contains HTML content.")
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)

    # Attachment
    if attachment_bytes and attachment_filename:
        mime_type, _ = mimetypes.guess_type(attachment_filename)
        maintype, subtype = (mime_type or "application/octet-stream").split("/")
        msg.add_attachment(
            attachment_bytes,
            maintype=maintype,
            subtype=subtype,
            filename=attachment_filename,
        )

    all_recipients = to_list + cc_list + bcc_list

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_password)

            mail_opts = []
            if request_dsn:
                mail_opts.append("NOTIFY=SUCCESS,FAILURE,DELAY")

            server.send_message(msg, to_addrs=all_recipients, mail_options=mail_opts)
            print("✅ Email sent successfully.")
            return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed. Check SMTP username/app password.")
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    return False
