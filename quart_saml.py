from quart import  url_for,current_app,session,request,redirect
from blinker import signal
import functools
import asyncio
import logging
import httpx
import saml2
import saml2.client
import saml2.config
import saml2.metadata
import urllib.parse as urlparse

__version__ = '0.1.0'

log = logging.getLogger(__name__)

saml_authenticated = signal('saml-authenticated')
saml_log_out = signal('saml-log-out')
saml_error = signal('saml-error')

async def _get_metadata(metadata_url):
    async with httpx.AsyncClient() as client:
        response = await client.get(metadata_url)
        if response.status_code != 200:
            exc = RuntimeError(
                'Unexpected Status Code: {0}'.format(response.status_code))
            exc.response = response
            raise exc
        return response.text
    
def _get_client(metadata, allow_unknown_attributes=True):
    acs_url = url_for('login_acs', _external=True)
    metadata_url = url_for('metadata', _external=True)
    settings = {
        'entityid': metadata_url,
        'metadata': {
            'inline': [metadata],
            },
        'service': {
            'sp': {
                'endpoints': {
                    'assertion_consumer_service': [
                        (acs_url, saml2.BINDING_HTTP_POST),
                    ],
                },
                # Don't verify that the incoming requests originate from us via
                # the built-in cache for authn request ids in pysaml2
                'allow_unsolicited': True,
                # Don't sign authn requests, since signed requests only make
                # sense in a situation where you control both the SP and IdP
                'authn_requests_signed': False,
                'logout_requests_signed': True,
                'want_assertions_signed': True,
                'want_response_signed': False,
            },
        },
    }
    config = saml2.config.Config()
    config.load(settings)
    config.allow_unknown_attributes = allow_unknown_attributes
    client = saml2.client.Saml2Client(config=config)
    return client


def _saml_prepare(wrapped_func):
    @functools.wraps(wrapped_func)
    async def func():
        ext, config = current_app.extensions['saml']
        client = _get_client(config['metadata'])
        return await wrapped_func(client)
    return func

def _session_login(sender,subject,attributes,auth):
    session['saml'] = {
        'subject': subject,
        'attributes': attributes,
    }

def _session_logout(sender):
    session.clear()

class QuartSAML(object):
    """
    The extension class. Refer to the documentation on its usage.

    :param app: The :class:`quart.Quart` app.
    :param bool debug: Enable debug mode for the extension.
    """

    def __init__(
            self, app=None, debug=False):
        self.app = app
        self._debug = debug
        if self.app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('SAML_PREFIX', '/saml')
        app.config.setdefault('SAML_DEFAULT_REDIRECT', '/')
        app.config.setdefault('SAML_USE_SESSIONS', True)

        config = {
            'metadata': asyncio.run(_get_metadata(
                metadata_url=app.config['SAML_METADATA_URL'],
            )),
            'prefix': app.config['SAML_PREFIX'],
            'default_redirect': app.config['SAML_DEFAULT_REDIRECT'],
        }

        saml_routes = {
            'logout': logout,
            'sso': login,
            'acs': login_acs,
            'metadata': metadata,
        }
        for route, func in saml_routes.items():
            path = '%s/%s/' % (config['prefix'], route)
            app.add_url_rule(path, view_func=func, methods=['GET', 'POST'])

        # Register configuration on app so we can retrieve it later on
        if not hasattr(app, 'extensions'):  # pragma: no cover
            app.extensions = {}
        app.extensions['saml'] = self, config

        if app.config['SAML_USE_SESSIONS']:
            saml_authenticated.connect(_session_login, app)
            saml_log_out.connect(_session_logout, app)


def _get_return_to():
    ext, config = current_app.extensions['saml']
    return_to = request.args.get('next', '')
    if not return_to.startswith(request.url_root):
        return_to = config['default_redirect']
    return return_to

@_saml_prepare
async def logout(saml_client):
    log.debug('Received logout request')
    saml_log_out.send(
        current_app._get_current_object(),
    )
    ext, config = current_app.extensions['saml']
    url = request.url_root[:-1] + config['default_redirect']
    return redirect(url)

@_saml_prepare
async def login(saml_client):
    log.debug('Received login request')
    return_url = _get_return_to()
    reqid, info = saml_client.prepare_for_authenticate(
        relay_state=return_url,
    )
    headers = dict(info['headers'])
    response = redirect(headers.pop('Location'), code=302)
    for name, value in headers.items():
        response.headers[name] = value
    response.headers['Cache-Control'] = 'no-cache, no-store'
    response.headers['Pragma'] = 'no-cache'
    return response

@_saml_prepare
async def login_acs(saml_client):
    form_data = await request.form
    if 'SAMLResponse' in form_data:
        log.debug('Received SAMLResponse for login')
        try:
            authn_response = saml_client.parse_authn_request_response(
                form_data['SAMLResponse'],
                saml2.entity.BINDING_HTTP_POST,
            )
            if authn_response is None:
                raise RuntimeError('Unknown SAML error, please check logs')
        except Exception as exc:
            saml_error.send(
                current_app._get_current_object(),
                exception=exc,
            )
        else:
            saml_authenticated.send(
                current_app._get_current_object(),
                subject=authn_response.get_subject().text,
                attributes=authn_response.get_identity(),
                auth=authn_response,
            )
        relay_state = form_data.get('RelayState')
        ext, config = current_app.extensions['saml']
        if not relay_state:
            relay_state = config['default_redirect']
        redirect_to = relay_state
        if not relay_state.startswith(request.url_root):
            redirect_to = request.url_root[:-1] + redirect_to
        return redirect(redirect_to)
    return 'Missing SAMLResponse POST data', 500

@_saml_prepare
async def metadata(saml_client):
    metadata_str = saml2.metadata.create_metadata_string(
        configfile=None,
        config=saml_client.config,
    )
    return metadata_str, {'Content-Type': 'text/xml'}

