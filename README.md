# Quart SAML

This Quart extension provides you with an easy way to integrate SAML into
your Quart web app.

## Installation


Beyond installing the library (e.g. ``pip install quart_saml``) you need to have ``xmlsec1`` installed, e.g. for Ubuntu:

```bash
apt-get install xmlsec1
```

## Quickstart

```python
from quart import Quart , url_for,redirect,session
import quart_saml

app = quart.Quart(__name__)

app.config.update({
    'SECRET_KEY': 'somethingsecret',
    'SAML_METADATA_URL': 'https://mymetadata.xml',
})

quart_saml.QuartSAML(app)

@app.route("/")
async def home():
    if "saml" in session:
        return "<p>Helo world</p>"
    else:
        return redirect(url_for("login"))
```

The ``SECRET_KEY`` is required by the default session
storage. The  ``SAML_METADATA_URL`` is a URL that contains the
SAML metadata which configures the whole app.
Upon successful authentication the user info is stored in session storage under the key 'saml'. The structure of the session data is as follows:
```python
{
    'saml': {
        'subject': 'user@example.com',  # User's unique identifier from the SAML response
        'attributes': {}  # Additional attributes provided in the SAML assertion
    }
}
```

>[!WARNING]
>The metadata URL should be a HTTPS URL as an untrusted source for metadata
will allow an attacker to log in as any user they like.


The extension also sets up the following routes:

* ``/saml/logout/``: Log out from the application. This is where users
  go if they click on a "Logout" button.
* ``/saml/sso/``: Log in through SAML.
* ``/saml/acs/``: After ``/saml/sso/`` has sent you to your IdP it sends you
  back to this path. Also your IdP might provide direct login without needing
  the ``/saml/sso/`` route.

Sending users to login
and logout is as simple as calling ``quart.url_for('login')`` and
``quart.url_for('logout')``

## Acknowledgments

This project is based on the [Flask-SAML](https://pypi.org/project/Flask-SAML/) extension. For those looking to integrate SAML with Flask, it serves as an excellent resource.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/nojha95/quart_saml/blob/main/LICENSE.txt) file for details.









