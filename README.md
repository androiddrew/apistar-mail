# apistar-mail

[![Build Status](https://travis-ci.org/androiddrew/apistar-mail.svg?branch=master)](https://travis-ci.org/androiddrew/apistar-mail)
[![codecov](https://codecov.io/gh/androiddrew/apistar-mail/branch/master/graph/badge.svg)](https://codecov.io/gh/androiddrew/apistar-mail)


Provides a simple interface to set up SMTP with your [APIStar](https://github.com/encode/apistar) application and send messages from your view functions. Please note this work derives largely from the [Flask-Mail](https://github.com/mattupstate/flask-mail) extension by 'Dan Jacob' and contributors, but has been modified extensively to remove Python 2 support and be used as an APIStar component.


## Installation

`$  pip install apistar-mail`

## Usage

### Example Setup

To send mail messages from your view functions you must include the 'MAIL' dictionary in your settings, the mail_component in your component list, and the Mail component as a dependency in your view. Here we have a minimally viable app capable of sending an email message and returning a 204 response code:

```python
from apistar import Route
from apistar.frameworks.wsgi import WSGIApp as App
from apistar_mail import mail_component, Mail, Message

settings = {
    'MAIL': {
        'MAIL_SERVER': 'smtp.example.com',
        'MAIL_USERNAME': 'me@example.com',
        'MAIL_PASSWORD': 'dontcommitthistoversioncontrol',
        'MAIL_PORT': 587,
        'MAIL_USE_TLS': True,
        'MAIL_DEFAULT_SENDER': 'me@example.com'
    }
}


def send_a_message(mail: Mail):
    msg = Message('Hello',
                  sender='me@example.com',
                  recipients=['you@example.com'])
    mail.send(msg)
    return


routes = [
    Route('/', 'POST', send_a_message)
]

components = [
    mail_component
]

app = App(
    settings=settings,
    routes=routes,
    components=components
)

if __name__ == '__main__':
    app.main()

```

### Sending Messages

To send a message ,first include the Mail component for injection into your view. Then create an instance of Message, and pass it to your Mail component using `mail.send(msg)`

```python
from apistar_mail import Mail, Message

def send_a_message(mail:Mail):
    msg = Message('Hello',
                  sender='drew@example.com',
                  recipients=['you@example.com'])
    mail.send(msg)
    return
```

Your message recipients can be set in bulk or individually:

```python
msg.recipients = ['you@example.com', 'me@example.com']
msg.add_recipient('otherperson@example.com')
```

If you have set `MAIL_DEFAULT_SENDER` you don’t need to set the message sender explicitly, as it will use this configuration value by default:

```python
msg = Message('Hello',
              recipients=['you@example.com'])
```

The sender can also be passed as a two element tuple containing a name and email address which will be split like so:

```python
msg = Message('Hello',
              sender=('Me', 'me@example.com'))

assert msg.sender == 'Me <me@example.com>'
```

A Message can contain a body and/or HTML:

```python
msg.body = 'message body'
msg.html = '<b>Hello apistar_mail!</b>'
```

### Configuration Options

apistar-mail is configured through the inclusion of the `MAIL` dictionary in your apistar settings. These are the available options:

* 'MAIL_SERVER': default 'localhost'
* 'MAIL_USERNAME': default None
* 'MAIL_PASSWORD': default None
* 'MAIL_PORT': default 25
* 'MAIL_USE_TLS': default False
* 'MAIL_USE_SSL': default False
* 'MAIL_DEFAULT_SENDER': default None
* 'MAIL_DEBUG': default False
* 'MAIL_MAX_EMAILS': default None
* 'MAIL_SUPPRESS_SEND': default False
* 'MAIL_ASCII_ATTACHMENTS': False


## Testing

To run the test suite with coverage first install the package in editable mode with it's testing requirements:

`$ pip install -e ".[testing]"`

To run the project's tests

`$ pytest --cov`

To run tests against multiple python interpreters use:

`$ tox`