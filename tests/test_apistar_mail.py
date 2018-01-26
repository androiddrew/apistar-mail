import base64
import email
import re
import time
from apistar_mail.mail import Message, Mail, force_text, sanitize_address
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

# Message

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


def test_esmtp_options_properly_initialized():
    msg = Message(subject='subject')
    assert msg.mail_options == []
    assert msg.rcpt_options == []


def test_sender_as_tuple():
    msg = Message(subject='test',
                  sender=('Me', 'me@example.com'))
    assert msg.sender == 'Me <me@example.com>'


def test_emails_are_sanitized():
    msg = Message(subject="testing",
                  sender="sender\r\n@example.com",
                  reply_to="reply_to\r\n@example.com",
                  recipients=["recipient\r\n@example.com"])
    assert 'sender@example.com' in msg.as_string()
    assert 'reply_to@example.com' in msg.as_string()
    assert 'recipient@example.com' in msg.as_string()


def test_plain_message():
    plain_text = "Hello Joe,\nHow are you?"
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["to@example.com"],
                  body=plain_text)
    assert plain_text == msg.body
    assert 'Content-Type: text/plain' in msg.as_string()


def test_message_str():
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["to@example.com"],
                  body="some plain text")
    assert msg.as_string() == str(msg)


def test_plain_message_with_attachments():
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["to@example.com"],
                  body="hello")

    msg.attach(data=b"this is a test",
               content_type="text/plain")

    assert 'Content-Type: multipart/mixed' in msg.as_string()


def test_plain_message_with_ascii_attachment():
    msg = Message(subject="subject",
                  recipients=["to@example.com"],
                  body="hello",
                  sender="me@example.com", )

    msg.attach(data=b"this is a test",
               content_type="text/plain",
               filename='test doc.txt')

    assert 'Content-Disposition: attachment; filename="test doc.txt"' in msg.as_string()


def test_plain_message_with_unicode_attachment():
    msg = Message(subject="subject",
                  recipients=["to@example.com"],
                  body="hello",
                  sender="me@example.com", )

    msg.attach(data=b"this is a test",
               content_type="text/plain",
               filename='ünicöde ←→ ✓.txt')

    parsed = email.message_from_string(msg.as_string())

    assert re.sub(r'\s+', ' ', parsed.get_payload()[1].get('Content-Disposition')) in [
        'attachment; filename*="UTF8\'\'%C3%BCnic%C3%B6de%20%E2%86%90%E2%86%92%20%E2%9C%93.txt"',
        'attachment; filename*=UTF8\'\'%C3%BCnic%C3%B6de%20%E2%86%90%E2%86%92%20%E2%9C%93.txt'
    ]


def test_plain_message_with_ascii_converted_attachment():
    msg = Message(subject="subject",
                  recipients=["to@example.com"],
                  body="hello",
                  sender="me@example.com",
                  ascii_attachments=True)

    msg.attach(data=b"this is a test",
               content_type="text/plain",
               filename='ünicödeß ←.→ ✓.txt')

    assert 'Content-Disposition: attachment; filename="unicode . .txt"' in msg.as_string()


def test_html_message():
    html_text = "<p>Hello World</p>"
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["to@example.com"],
                  html=html_text)

    assert html_text == msg.html
    assert 'Content-Type: multipart/alternative' in msg.as_string()


def test_json_message():
    json_text = '{"msg": "Hello World!}'
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["to@example.com"],
                  alts={'json': json_text})

    assert json_text == msg.alts['json']
    assert 'Content-Type: multipart/alternative' in msg.as_string()


def test_html_message_with_attachments():
    html_text = "<p>Hello World</p>"
    plain_text = 'Hello World'
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["to@example.com"],
                  body=plain_text,
                  html=html_text)
    msg.attach(data=b"this is a test",
               content_type="text/plain")

    assert html_text == msg.html
    assert 'Content-Type: multipart/alternative' in msg.as_string()

    parsed = email.message_from_string(msg.as_string())
    assert len(parsed.get_payload()) == 2

    body, attachment = parsed.get_payload()
    assert len(body.get_payload()) == 2

    plain, html = body.get_payload()
    assert plain.get_payload() == plain_text
    assert html.get_payload() == html_text
    assert base64.b64decode(attachment.get_payload()), b'this is a test'


def test_date_header():
    before = time.time()
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["to@example.com"],
                  body="hello",
                  date=time.time())
    after = time.time()

    assert before <= msg.date <= after
    date_formatted = email.utils.formatdate(msg.date, localtime=True)
    assert 'Date: ' + date_formatted in msg.as_string()


def test_msgid_header():
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["to@example.com"],
                  body="hello")

    # see RFC 5322 section 3.6.4. for the exact format specification
    r = re.compile(r"<\S+@\S+>").match(msg.msgId)
    assert r is not None
    assert 'Message-ID: ' + msg.msgId in msg.as_string()


def test_unicode_sender_tuple():
    msg = Message(subject="subject",
                  sender=("ÄÜÖ → ✓", 'from@example.com>'),
                  recipients=["to@example.com"])

    assert 'From: =?utf-8?b?w4TDnMOWIOKGkiDinJM=?= <from@example.com>' in msg.as_string()


def test_unicode_sender():
    msg = Message(subject="subject",
                  sender='ÄÜÖ → ✓ <from@example.com>>',
                  recipients=["to@example.com"])

    assert 'From: =?utf-8?b?w4TDnMOWIOKGkiDinJM=?= <from@example.com>' in msg.as_string()


def test_unicode_headers():
    msg = Message(subject="subject",
                  sender='ÄÜÖ → ✓ <from@example.com>',
                  recipients=["Ä <t1@example.com>", "Ü <t2@example.com>"],
                  cc=["Ö <cc@example.com>"])

    response = msg.as_string()
    a1 = sanitize_address("Ä <t1@example.com>")
    a2 = sanitize_address("Ü <t2@example.com>")
    h1_a = email.header.Header("To: %s, %s" % (a1, a2))
    h1_b = email.header.Header("To: %s, %s" % (a2, a1))
    h2 = email.header.Header("From: %s" % sanitize_address("ÄÜÖ → ✓ <from@example.com>"))
    h3 = email.header.Header("Cc: %s" % sanitize_address("Ö <cc@example.com>"))

    # Ugly, but there's no guaranteed order of the recipients in the header
    try:
        assert h1_a.encode() in response
    except AssertionError:
        assert h1_b.encode() in response

    assert h2.encode() in response
    assert h3.encode() in response


def test_unicode_subject():
    msg = Message(subject="sübject",
                  sender='from@example.com',
                  recipients=["to@example.com"])
    assert '=?utf-8?q?s=C3=BCbject?=' in msg.as_string()


def test_extra_headers():
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["to@example.com"],
                  body="hello",
                  extra_headers={'X-Extra-Header': 'Yes'})
    assert 'X-Extra-Header: Yes' in  msg.as_string()


def test_message_charset():
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["foo@bar.com"],
                  charset='us-ascii')

    # ascii body
    msg.body = "normal ascii text"
    assert 'Content-Type: text/plain; charset="us-ascii"' in msg.as_string()

    # ascii html
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["foo@bar.com"],
                  charset='us-ascii')
    msg.body = None
    msg.html = "<html><h1>hello</h1></html>"
    assert 'Content-Type: text/html; charset="us-ascii"' in msg.as_string()

    # unicode body
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["foo@bar.com"])
    msg.body = "ünicöde ←→ ✓"
    assert 'Content-Type: text/plain; charset="utf-8"' in msg.as_string()

    # unicode body and unicode html
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["foo@bar.com"])
    msg.html = "ünicöde ←→ ✓"
    assert 'Content-Type: text/plain; charset="utf-8"' in msg.as_string()
    assert 'Content-Type: text/html; charset="utf-8"' in msg.as_string()

    # unicode body and attachments
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["foo@bar.com"])
    msg.html = None
    msg.attach(data=b"foobar", content_type='text/csv')
    assert 'Content-Type: text/plain; charset="utf-8"' in msg.as_string()

    # unicode sender as tuple
    msg = Message(sender=("送信者", "from@example.com"),
                  subject="表題",
                  recipients=["foo@bar.com"],
                  reply_to="返信先 <somebody@example.com>",
                  charset='shift_jis')  # japanese
    msg.body = '内容'
    assert 'From: =?iso-2022-jp?' in msg.as_string()
    assert 'From: =?utf-8?' not in msg.as_string()
    assert 'Subject: =?iso-2022-jp?' in msg.as_string()
    assert 'Subject: =?utf-8?' not in msg.as_string()
    assert 'Reply-To: =?iso-2022-jp?' in msg.as_string()
    assert 'Reply-To: =?utf-8?' not in msg.as_string()
    assert 'Content-Type: text/plain; charset="iso-2022-jp"' in msg.as_string()

    # unicode subject sjis
    msg = Message(sender="from@example.com",
                  subject="表題",
                  recipients=["foo@bar.com"],
                  charset='shift_jis')  # japanese
    msg.body = '内容'
    assert 'Subject: =?iso-2022-jp?' in msg.as_string()
    assert 'Content-Type: text/plain; charset="iso-2022-jp"', msg.as_string()

    # unicode subject utf-8
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["foo@bar.com"],
                  charset='utf-8')
    msg.body = '内容'
    assert 'Subject: subject' in msg.as_string()
    assert 'Content-Type: text/plain; charset="utf-8"' in msg.as_string()

    # ascii subject
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["foo@bar.com"],
                  charset='us-ascii')
    msg.body = "normal ascii text"
    assert 'Subject: =?us-ascii?' not in msg.as_string()
    assert 'Content-Type: text/plain; charset="us-ascii"' in msg.as_string()

    # default charset
    msg = Message(sender="from@example.com",
                  subject="subject",
                  recipients=["foo@bar.com"])
    msg.body = "normal ascii text"
    assert 'Subject: =?' not in msg.as_string()
    assert 'Content-Type: text/plain; charset="utf-8"' in msg.as_string()


def test_empty_subject_header():
    mail = Mail(settings)
    msg = Message(sender="from@example.com",
                  recipients=["foo@bar.com"])
    msg.body = "normal ascii text"
    mail.send(msg)
    assert 'Subject:' not in msg.as_string()
