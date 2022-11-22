from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.template.loader import render_to_string


class Command(BaseCommand):
    """Generate configuration for quick setup third-party systems like nginx and gunicorn."""
    help = 'Generate configuration'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options = {
            'nginx': self._gen_nginx_config,
            'gunicorn': self._gen_gunicorn_config,
        }

    def add_arguments(self, parser):
        """Add custom arguments to command parser."""
        parser.add_argument('conf_id', choices=list(self.options.keys()))

    @staticmethod
    def _gen_nginx_config() -> str:
        if not settings.STATIC_ROOT:
            raise CommandError('No settings.STATIC_ROOT')

        context = {'settings': settings}
        return render_to_string('config/nginx.conf', context=context)

    @staticmethod
    def _gen_gunicorn_config() -> str:
        context = {'settings': settings}
        return render_to_string('config/gunicorn.conf.py', context=context)

    def handle(self, *args, conf_id, **options):
        """Run config generator."""
        self.stdout.write(self.options[conf_id]())
