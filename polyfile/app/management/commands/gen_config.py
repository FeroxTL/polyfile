from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.template.loader import render_to_string


class Command(BaseCommand):
    help = 'Generate configuration'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options = {
            'nginx': self.gen_nginx_config,
            'gunicorn': self.gen_gunicorn_config,
        }

    def add_arguments(self, parser):
        parser.add_argument('conf_id', choices=list(self.options.keys()))

    @staticmethod
    def gen_nginx_config() -> str:
        if not settings.STATIC_ROOT:
            raise CommandError('No settings.STATIC_ROOT')

        context = {'settings': settings}
        return render_to_string('config/nginx.conf', context=context)

    @staticmethod
    def gen_gunicorn_config() -> str:
        context = {'settings': settings}
        return render_to_string('config/gunicorn.conf.py', context=context)

    def handle(self, *args, conf_id, **options):
        self.stdout.write(self.options[conf_id]())
