import re
import smtplib
import time
import unicodedata

from email import charset, policy
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate, formataddr, make_msgid, parseaddr

from apistar import Settings, Component

from .exc import MailUnicodeDecodeError, BadHeaderError

charset.add_charset('utf-8', charset.SHORTEST, None, 'utf-8')


def force_text(s, encoding='utf-8', errors='strict', ):
    if isinstance(s, str):
        return s

    try:
        if not isinstance(s, str):
            if isinstance(s, bytes):
                s = s.decode(encoding, errors)
            else:
                s = str(s)

    except UnicodeDecodeError as e:
        try:
            if not isinstance(s, Exception):
                raise MailUnicodeDecodeError(s, *e.args)
            else:
                s = ' '.join([force_text(arg, encoding, errors) for arg in s])
        except UnicodeDecodeError as e:
            raise MailUnicodeDecodeError(s, *e.args)

    return s


def sanitize_subject(subject, encoding='utf-8'):
    try:
        subject.encode('ascii')
    except UnicodeEncodeError:
        try:
            subject = Header(subject, encoding).encode()
        except UnicodeEncodeError:
            subject = Header(subject, 'utf-8').encode()
    return subject


def sanitize_address(addr, encoding='utf-8'):
    if isinstance(addr, str):
        addr = parseaddr(force_text(addr))
    nm, addr = addr

    try:
        nm = Header(nm, encoding).encode()
    except UnicodeEncodeError:
        nm = Header(nm, 'utf-8').encode()
    try:
        addr.encode('ascii')
    except UnicodeEncodeError:  # IDN
        if '@' in addr:
            localpart, domain = addr.split('@', 1)
            localpart = Header(localpart, encoding).encode()
            domain = domain.encode('idna').decode('ascii')
            addr = '@'.join([localpart, domain])
        else:
            addr = Header(addr, encoding).encode()
    return formataddr((nm, addr))


def sanitize_addresses(addresses, encoding='utf-8'):
    return map(lambda e: sanitize_address(e, encoding), addresses)


def _has_newline(line):
    """Used by has_bad_header to check for \\r or \\n"""
    if line and ('\r' in line or '\n' in line):
        return True
    return False


class Attachment:
    """Encapsulates file attachment information.

    :param filename: filename of attachment
    :param content_type: file mimetype
    :param data: the raw file data
    :param disposition: content-disposition (if any)
    :param headers: additional headers. Useful when HTML emails reference attached images
    """

    def __init__(self, filename=None, content_type=None, data=None,
                 disposition=None, headers=None):
        self.filename = filename
        self.content_type = content_type
        self.data = data
        self.disposition = disposition or 'attachment'
        self.headers = headers or {}


class Message:
    """Encapsulates an email message.

    :param subject: email subject header
    :param recipients: list of email addresses
    :param body: plain text message
    :param html: HTML message
    :param alts: A dict or an iterable to go through dict() that contains multipart alternatives
    :param sender: email sender address, or **MAIL_DEFAULT_SENDER** by default
    :param cc: CC list
    :param bcc: BCC list
    :param attachments: list of Attachment instances
    :param reply_to: reply-to address
    :param date: send date
    :param charset: message character set
    :param extra_headers: A dictionary of additional headers for the message
    :param mail_options: A list of ESMTP options to be used in MAIL FROM command
    :param rcpt_options:  A list of ESMTP options to be used in RCPT commands
    :param ascii_attachments: A boolean used to force attachment file names to ascii

    """

    def __init__(self, subject='',
                 recipients=None,
                 body=None,
                 html=None,
                 alts=None,
                 sender=None,
                 cc=None,
                 bcc=None,
                 attachments=None,
                 reply_to=None,
                 date=None,
                 charset=None,
                 extra_headers=None,
                 mail_options=None,
                 rcpt_options=None,
                 ascii_attachments=False):

        if isinstance(sender, tuple):
            sender = "{} <{}>".format(*sender)

        self.recipients = recipients or []
        self.subject = subject
        self.sender = sender
        self.reply_to = reply_to
        self.cc = cc or []
        self.bcc = bcc or []
        self.body = body
        self.alts = dict(alts or {})
        self.html = html
        self.date = date
        self.msgId = make_msgid()
        self.charset = charset
        self.extra_headers = extra_headers
        self.mail_options = mail_options or []
        self.rcpt_options = rcpt_options or []
        self.attachments = attachments or []
        self.ascii_attachments = ascii_attachments

    @property
    def send_to(self):
        return set(self.recipients) | set(self.bcc or ()) | set(self.cc or ())

    @property
    def html(self):
        return self.alts.get('html')

    @html.setter
    def html(self, value):
        if value is None:
            self.alts.pop('html', None)
        else:
            self.alts['html'] = value

    def _mimetext(self, text, subtype='plain'):
        """Creates a MIMEText object with the given subtype (default: 'plain')
        If the text is unicode, the utf-8 charset is used.
        """
        charset = self.charset or 'utf-8'
        return MIMEText(text, _subtype=subtype, _charset=charset)

    def _message(self):
        """Creates the email"""
        encoding = self.charset or 'utf-8'

        attachments = self.attachments or []

        if len(attachments) == 0 and not self.alts:
            # No html content and zero attachments means plain text
            msg = self._mimetext(self.body)
        elif len(attachments) > 0 and not self.alts:
            # No html and at least one attachment means multipart
            msg = MIMEMultipart()
            msg.attach(self._mimetext(self.body))
        else:
            # Anything else
            msg = MIMEMultipart()
            alternative = MIMEMultipart('alternative')
            alternative.attach(self._mimetext(self.body, 'plain'))
            for mimetype, content in self.alts.items():
                alternative.attach(self._mimetext(content, mimetype))
            msg.attach(alternative)

        if self.subject:
            msg['Subject'] = sanitize_subject(force_text(self.subject), encoding)

        msg['From'] = sanitize_address(self.sender, encoding)
        msg['To'] = ', '.join(list(set(sanitize_addresses(self.recipients, encoding))))

        msg['Date'] = formatdate(self.date, localtime=True)
        # see RFC 5322 section 3.6.4.
        msg['Message-ID'] = self.msgId

        if self.cc:
            msg['Cc'] = ', '.join(list(set(sanitize_addresses(self.cc, encoding))))

        if self.reply_to:
            msg['Reply-To'] = sanitize_address(self.reply_to, encoding)

        if self.extra_headers:
            for k, v in self.extra_headers.items():
                msg[k] = v

        SPACES = re.compile(r'[\s]+', re.UNICODE)
        for attachment in attachments:
            f = MIMEBase(*attachment.content_type.split('/'))
            f.set_payload(attachment.data)
            encode_base64(f)

            filename = attachment.filename
            if filename and self.ascii_attachments:
                # force filename to ascii
                filename = unicodedata.normalize('NFKD', filename)
                filename = filename.encode('ascii', 'ignore').decode('ascii')
                filename = SPACES.sub(u' ', filename).strip()

            try:
                filename and filename.encode('ascii')

            except UnicodeEncodeError:
                filename = ('UTF8', '', filename)

            f.add_header('Content-Disposition',
                         attachment.disposition,
                         filename=filename)

            for key, value in attachment.headers.items():
                f.add_header(key, value)

            msg.attach(f)

        msg.policy = policy.SMTP

        return msg

    def as_string(self):
        return self._message().as_string()

    def as_bytes(self):
        return self._message().as_bytes()

    def __str__(self):
        return self.as_string()

    def __bytes__(self):
        return self.as_bytes()

    def has_bad_headers(self):
        """Checks for bad headers i.e. newlines in subject, sender or recipients.
        RFC5322: Allows multiline CRLF with trailing whitespace (FWS) in headers
        """

        headers = [self.sender, self.reply_to] + self.recipients
        for header in headers:
            if _has_newline(header):
                return True

        if self.subject:
            if _has_newline(self.subject):
                for linenum, line in enumerate(self.subject.split('\r\n')):
                    if not line:
                        return True
                    if linenum > 0 and line[0] not in '\t ':
                        return True
                    if _has_newline(line):
                        return True
                    if len(line.strip()) == 0:
                        return True
        return False

    def send(self, connection):
        """Verifies and sends the message."""

        connection.send(self)

    def add_recipient(self, recipient):
        """Adds another recipient to the message.

        :param recipient: email address of recipient.
        """

        self.recipients.append(recipient)

    def attach(self,
               filename=None,
               content_type=None,
               data=None,
               disposition=None,
               headers=None):
        """Adds an attachment to the message.

        :param filename: filename of attachment
        :param content_type: file mimetype
        :param data: the raw file data
        :param disposition: content-disposition (if any)
        :param headers: additional headers. Useful when HTML emails reference attached images

        """
        self.attachments.append(
            Attachment(filename, content_type, data, disposition, headers))


class Connection:
    """Handles connection to host"""

    def __init__(self, mail):
        """
        configure new connection

        :param mail: the application mail manager
        """
        self.mail = mail

    def __enter__(self):
        if self.mail.mail_suppress_send:
            self.host = None
        else:
            self.host = self.configure_host()

        self.num_emails = 0

        return self

    def __exit__(self, exc_type, exc_value, tb):
        if self.host:
            self.host.quit()

    def configure_host(self):
        if self.mail.mail_use_ssl:
            host = smtplib.SMTP_SSL(self.mail.mail_server, self.mail.mail_port)
        else:
            host = smtplib.SMTP(self.mail.mail_server, self.mail.mail_port)

        host.set_debuglevel(int(self.mail.mail_debug))

        if self.mail.mail_use_tls:
            host.starttls()
        if self.mail.mail_user and self.mail.mail_password:
            host.login(self.mail.mail_user, self.mail.mail_password)

        return host

    def send(self, message, envelope_from=None):
        """Verifies and sends message.

        :param message: Message instance.
        :param envelope_from: Email address to be used in MAIL FROM command.
        """
        assert message.send_to, "No recipients have been added"

        assert message.sender, (
            "The message does not specify a sender and a default sender "
            "has not been configured")

        if message.has_bad_headers():
            raise BadHeaderError

        if message.date is None:
            message.date = time.time()

        if not message.ascii_attachments and self.mail.mail_ascii_attachments:
            message.ascii_attachments = True

        if self.host:
            self.host.sendmail(sanitize_address(envelope_from or message.sender),
                               list(sanitize_addresses(message.send_to)),
                               message.as_bytes(),
                               message.mail_options,
                               message.rcpt_options)

            self.num_emails += 1

            if self.num_emails == self.mail.mail_max_emails:
                self.num_emails = 0
                if self.host:
                    self.host.quit()
                    self.host = self.configure_host()

    def send_message(self, *args, **kwargs):
        """Shortcut for send(msg).

        Takes same arguments as Message constructor.
        """

        self.send(Message(*args, **kwargs))


class Mail:
    """Manages email messaging"""

    def __init__(self, settings: Settings):
        """
        Configure a new Mail manager

        Args:
        settings: The application settings dictionary
        """
        mail_config = settings.get('MAIL')
        self.mail_server = mail_config.get('MAIL_SERVER', 'localhost')
        self.mail_user = mail_config.get('MAIL_USERNAME')
        self.mail_password = mail_config.get('MAIL_PASSWORD')
        self.mail_port = mail_config.get('MAIL_PORT', 25)
        self.mail_use_tls = mail_config.get('MAIL_USE_TLS', False)
        self.mail_use_ssl = mail_config.get('MAIL_USE_SSL', False)
        self.mail_default_sender = mail_config.get('MAIL_DEFAULT_SENDER')
        self.mail_debug = mail_config.get('MAIL_DEBUG', False)
        self.mail_max_emails = mail_config.get('MAIL_MAX_EMAILS')
        self.mail_suppress_send = mail_config.get('MAIL_SUPPRESS_SEND', False)
        self.mail_ascii_attachments = mail_config.get('MAIL_ASCII_ATTACHMENTS', False)

    def send(self, message):
        """
        Sends a single message instance. If TESTING is True the message will
        not actually be sent.

        :param message: a Message instance.
        """
        if message.sender is None:
            message.sender = self.mail_default_sender

        with self.connect() as connection:
            message.send(connection)

    def send_message(self, *args, **kwargs):
        """Shortcut for send(msg).

        Takes same arguments as Message constructor.
        """

        self.send(Message(*args, **kwargs))

    def connect(self):
        """Opens a connection to the mail host."""
        return Connection(self)


mail_component = Component(Mail, preload=True)
