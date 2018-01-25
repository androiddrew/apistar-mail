# apistar-mail
---

 `apistar-mail` provides a simple interface to set up SMTP with your APIStar application and send messages from your view functions. Please note this work derives largely from the [flask_mail](https://github.com/mattupstate/flask-mail) extension by 'Dan Jacob' but has been modified extensively to remove Python 2 support and be used as an APIStar component.


## Installation

`$  pip install apistar-mail`

## Usage

### Setup

To send mail messages from your view functions you must include the `MAIL` dictionary in your settings and the mail_component in your component list.

```
from apistar import WSGIApp as App
from apistar_mail import mail_component

settings = {
    'MAIL': {
        'MAIL_SERVER': 'smtp.example.com',
        'MAIL_USERNAME': 'drew@example.com',
        'MAIL_PASSWORD': 'dontcommitthistoversioncontrol',
        'MAIL_PORT': 587,
        'MAIL_USE_TLS': True,
        'MAIL_DEFAULT_SENDER': 'drew@example.com'
    }
}

components = [
    mail_component
]

app = App(
    settings=settings,
    routes=routes,
    components=components
)

```

### Sending Messages

To send a message first include the Mail component for injection into your view. Then create an instance of Message, and pass it to your Mail component using `mail.send(msg)`

```
from apistar_mail import Mail, Message

def send_a_message(mail:Mail):
    msg = Message('Hello',
                  sender='drew@example.com'
                  recipients=[you@example.com])
    mail.send(msg)
    return
```


