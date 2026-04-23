from django.apps import AppConfig


class RequestsConfig(AppConfig):
    name = 'requests'

    def ready(self):
        # Import signals to ensure they are registered when the app is ready
        import requests.signals
