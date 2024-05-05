from django.core.mail.backends.smtp import EmailBackend

from site_configuration.models import EmailConfiguration


class DynamicSMPTEmailBackend(EmailBackend):
    # pylint: disable-next=too-many-arguments
    def __init__(
        self,
        host=None,
        port=None,
        username=None,
        password=None,
        use_tls=None,
        fail_silently=False,
        use_ssl=None,
        timeout=None,
        ssl_keyfile=None,
        ssl_certfile=None,
        **kwargs,
    ):
        conf = EmailConfiguration.get_solo()

        super().__init__(
            host=host or conf.host,
            port=port or conf.port,
            username=username or conf.username,
            password=password or conf.password,
            use_tls=use_tls or conf.use_tls,
            fail_silently=fail_silently,
            use_ssl=use_ssl or conf.use_ssl,
            timeout=timeout or conf.timeout,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            **kwargs,
        )
