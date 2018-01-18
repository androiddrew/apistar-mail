import email
import smtplib
import typing


class Connection:
    """Handles connection to host"""
    pass


class Attachment:
    """Encapsulates file attachment information"""
    pass


class Message:
    """Encapsulates an email message"""

    def __init__(self, subject: str,
                 recipients: typing.List[str]=None):
        self.subject = subject
        self.recipients = recipients or []

    def add_recipient(self, recipient: str):
        assert isinstance(recipient, str)
        self.recipients.append(recipient)


class _MailMixin:
    pass


class _Mail:
    pass


class Mail:
    """Manages email messaging"""
    pass
