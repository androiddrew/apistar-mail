from apistar_mail.mail import Message, Mail, force_text
from apistar_mail.exc import MailUnicodeDecodeError

import pytest

settings = {
    'MAIL': {
        'MAIL_SERVER': 'smtp.example.com',
        'MAIL_USERNAME': 'fake@example.com',
        'MAIL_PASSWORD': 'secret',
        'MAIL_PORT': 587,
        'MAIL_USE_TLS': True,
        'MAIL_SUPPRESS_SEND': True,
        'MAIL_DEFAULT_SENDER': 'fake@example.com'
    }
}


def test_message_init():
    msg = Message(subject="subject",
                  recipients=["fake@example.com"],
                  body="body")
    assert msg.subject == "subject"
    assert msg.recipients == ["fake@example.com"]
    assert msg.body == "body"


def test_empty_recipient_list_init():
    msg = Message(subject="subject")
    assert msg.recipients == []


def test_add_recipient():
    msg1 = Message(subject="subject")
    assert msg1.recipients == []
    msg1.add_recipient("fake@example.com")
    assert len(msg1.recipients) == 1
    assert msg1.recipients[0] == "fake@example.com"


def test_empty_cc_list():
    msg = Message(subject="subject",
                  recipients=['fake@example.com']
                  )
    assert msg.cc == []


def test_raise_unicode_decode_error():
    value = b'\xe5\x93\x88\xe5\x93\x88'
    with pytest.raises(MailUnicodeDecodeError) as excinfo:
        force_text(value, encoding='ascii')
    assert 'You passed in' in str(excinfo)