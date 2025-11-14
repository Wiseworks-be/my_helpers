import smtplib
import mimetypes
from email.message import EmailMessage
from email.utils import formataddr
from datetime import datetime
from datetime import timezone
import logging
import os


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


def send_email(  # different login email from sender email!
    subject,
    body,
    from_email,  # Visible "From" address (NO-REPLY)
    from_name,
    smtp_user,  # Login identity (master@sisusync.app, support@wiseworks.be)
    smtp_password,  # App password of master@
    recipient_email,
    recipient_cc=None,
    recipient_bcc=None,
    reply_to=None,
    attachment_bytes=None,
    attachment_filename=None,
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    html_content=False,
):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"

    # Normalize addresses
    to_list = (
        [str(e) for e in recipient_email]
        if isinstance(recipient_email, list)
        else [str(recipient_email)]
    )
    cc_list = (
        [str(e) for e in recipient_cc]
        if isinstance(recipient_cc, list)
        else ([str(recipient_cc)] if recipient_cc else [])
    )
    bcc_list = (
        [str(e) for e in recipient_bcc]
        if isinstance(recipient_bcc, list)
        else ([str(recipient_bcc)] if recipient_bcc else [])
    )

    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    if reply_to:
        msg["Reply-To"] = reply_to

    # HTML vs text
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

    # Final recipients
    all_recipients = to_list + cc_list + bcc_list

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)  # ← LOGIN AS MASTER ONLY
            server.send_message(msg, to_addrs=all_recipients)
            print("✅ Email sent successfully.")
            return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed. Check SMTP username/app password.")
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    return False
