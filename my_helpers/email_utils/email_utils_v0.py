"""Email utilities for sending notifications and alerts."""
import smtplib
import mimetypes
from email.message import EmailMessage
from email.utils import formataddr
from datetime import datetime, timezone
import logging
import os
from my_helpers.errors import *


def send_email(
    subject,
    body,
    sender_email,
    sender_password,
    recipient_email,
    sender_name=None,
    recipient_cc=None,
    recipient_bcc=None,
    reply_to=None,
    attachment_bytes=None,
    attachment_filename=None,
    smtp_server="smtp.gmail.com",
    smtp_port=587,
):
    """
    Sends an email with optional attachments, CC, BCC, and reply-to.
    
    Parameters:
    - subject (str): Email subject line
    - body (str): Email body text
    - sender_email (str): Sender's email address
    - sender_password (str): Sender's app password
    - recipient_email (str or list): To recipient(s)
    - sender_name (str, optional): Display name for sender
    - recipient_cc (str or list, optional): CC recipient(s)
    - recipient_bcc (str or list, optional): BCC recipient(s)
    - reply_to (str, optional): Reply-to address
    - attachment_bytes (bytes, optional): File content as bytes
    - attachment_filename (str, optional): Filename for attachment
    - smtp_server (str): SMTP server address
    - smtp_port (int): SMTP port number
    
    Returns:
    - bool: True if email sent successfully, False otherwise
    """
    
    
    # Validate required parameters
    mandatory_args = {
        "subject": subject,
        "body": body,
        "sender_email": sender_email,
        "sender_password": sender_password,
        "recipient_email": recipient_email,
    }
    check_mandatory_args(mandatory_args)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = (
        formataddr((sender_name, sender_email)) if sender_name 
        else sender_email
    )

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

    msg.set_content(body)

    # Add attachment if provided
    if attachment_bytes and attachment_filename:
        mime_type, _ = mimetypes.guess_type(attachment_filename)
        maintype, subtype = (mime_type or "application/octet-stream").split("/")
        msg.add_attachment(
            attachment_bytes,
            maintype=maintype,
            subtype=subtype,
            filename=attachment_filename,
        )

    # Combine all recipients for sending
    all_recipients = to_list + cc_list + bcc_list

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg, to_addrs=all_recipients)
            return True
    except smtplib.SMTPAuthenticationError as e:
        from errors import log_error
        log_error(f"Email authentication failed: {e}")
        return False
    except smtplib.SMTPException as e:
        from errors import log_error
        log_error(f"SMTP error: {e}")
        return False
    except Exception as e:
        from errors import log_error
        log_error(f"Unexpected email error: {e}")
        return False


def send_error_alert_email(
    run_id,
    flow_name,
    error_details,
    sender_email,
    sender_password,
    recipient_email,
    sender_name="Flow Alert"
):
    """
    Send a standardized error alert email for application flows.
    
    Parameters:
    - run_id (str): Unique identifier for the flow run
    - flow_name (str): Name of the flow that failed
    - error_details (str): Details about the error
    - sender_email (str): Email address to send from
    - sender_password (str): App password for sender email
    - recipient_email (str): Email address to send to
    - sender_name (str): Display name for sender
    
    Returns:
    - bool: True if email sent successfully, False otherwise
    """
    subject = f"Flow Error Alert - {flow_name} (Run ID: {run_id})"
    body = f"""An error occurred in flow '{flow_name}' (Run ID: {run_id}).

Error details:
{error_details}

Timestamp: {datetime.now(timezone.utc).isoformat()}

Please check the logs and Firestore audit collection for more details.
"""
    
    return send_email(
        subject=subject,
        body=body,
        sender_email=sender_email,
        sender_password=sender_password,
        recipient_email=recipient_email,
        sender_name=sender_name
    )


def send_email_with_env_password(
    subject,
    body,
    sender_email,
    recipient_email,
    password_env_var="EMAIL_PASSWORD",
    **kwargs
):
    """
    Send email using password from environment variable.
    
    Parameters:
    - subject (str): Email subject
    - body (str): Email body
    - sender_email (str): Sender email address
    - recipient_email (str): Recipient email address
    - password_env_var (str): Environment variable name for password
    - **kwargs: Additional parameters for send_email()
    
    Returns:
    - bool: True if email sent successfully, False otherwise
    """
    password = os.environ.get(password_env_var)
    if not password:
        from errors import log_error
        log_error(f"Environment variable {password_env_var} is not set!")
        return False
    
    return send_email(
        subject=subject,
        body=body,
        sender_email=sender_email,
        sender_password=password,
        recipient_email=recipient_email,
        **kwargs
    )