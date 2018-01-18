from apistar_mail.mail import Message


def test_message_init():
    msg = Message(subject="subject",
                  recipients=['fake@example.com'])
    assert msg.subject == "subject"
    assert msg.recipients == ['fake@example.com']


def test_empty_recipient_list_init():
    msg1 = Message(subject="subject")
    assert msg1.recipients == []


def test_add_recipient():
    msg1 = Message(subject="subject")
    assert msg1.recipients == []
    msg1.add_recipient('fake@example.com')
    assert len(msg1.recipients) == 1
    assert msg1.recipients[0] == 'fake@example.com'