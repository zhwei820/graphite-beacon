import datetime as dt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP

from tornado import concurrent, gen

from graphite_beacon.handlers import LOGGER, TEMPLATES, AbstractHandler


class SMTPHandler(AbstractHandler):

    name = 'smtp'

    # Default options
    defaults = {
        'host': 'localhost',
        'port': 25,
        'username': None,
        'password': None,
        'from': 'beacon@graphite',
        'to': None,
        'use_tls': False,
        'html': True,
        'graphite_url': None,
    }

    def init_handler(self):
        """ Check self options. """
        assert self.options.get('host') and self.options.get('port'), "Invalid options"
        assert self.options.get('to'), 'Recipients list is empty. SMTP disabled.'
        if not isinstance(self.options['to'], (list, tuple)):
            self.options['to'] = [self.options['to']]

    @gen.coroutine
    def notify(self, level, *args, **kwargs):
        LOGGER.debug("Handler (%s) %s", self.name, level)

        msg = self.get_message(level, *args, **kwargs)
        msg['Subject'] = self.get_short(level, *args, **kwargs)
        msg['From'] = self.options['from']
        msg['To'] = ", ".join(self.options['to'])

        smtp = SMTP()
        yield smtp_connect(smtp, self.options['host'], self.options['port'])  # pylint: disable=no-value-for-parameter

        if self.options['use_tls']:
            yield smtp_starttls(smtp)  # pylint: disable=no-value-for-parameter

        if self.options['username'] and self.options['password']:
            yield smtp_login(smtp,  # pylint: disable=no-value-for-parameter
                             self.options['username'],
                             self.options['password'])

        try:
            LOGGER.debug("Send message to: %s", ", ".join(self.options['to']))
            LOGGER.debug(smtp.sendmail(self.options['from'], self.options['to'], msg.as_string()))
        except Exception as e:
            LOGGER.exception(e)

        finally:
            smtp.quit()

    def get_message(self, level, alert, value, target=None, ntype=None, rule=None):
        txt_tmpl = TEMPLATES[ntype]['text']
        ctx = dict(
            reactor=self.reactor, alert=alert, value=value, level=level, target=target,
            dt=dt, rule=rule, **self.options)
        msg = MIMEMultipart('alternative')
        _msg = txt_tmpl.generate(**ctx)
        if isinstance(_msg, bytes):
            _msg = _msg.decode("utf-8")
        plain = MIMEText((_msg), 'plain')
        msg.attach(plain)
        if self.options['html']:
            html_tmpl = TEMPLATES[ntype]['html']
            _msg = html_tmpl.generate(**ctx)
            if isinstance(_msg, bytes):
                _msg = _msg.decode("utf-8")

            html = MIMEText(_msg, 'html')
            msg.attach(html)
        return msg


@concurrent.return_future
def smtp_connect(smtp, host, port, callback):
    callback(smtp.connect(host, port))


@concurrent.return_future
def smtp_starttls(smtp, callback):
    callback(smtp.starttls())


@concurrent.return_future
def smtp_login(smtp, username, password, callback):
    callback(smtp.login(username, password))

#  pylama:ignore=E1120
