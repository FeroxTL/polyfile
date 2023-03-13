from django.conf import settings
from django.core.checks import Error, register, Tags


@register(Tags.staticfiles)
def check_webpack_assets_dir(app_configs, **kwargs):
    """Check that settings.WEBPACK_ASSETS_DIR exists."""
    errors = []
    if not settings.TESTING and not settings.WEBPACK_ASSETS_DIR.exists():
        errors.append(
            Error(
                'polyfile requires the WEBPACK_ASSETS_DIR directory to exist.',
                hint='Set DEBUG=False or build frontend app.',
                id='polyfile.staticfiles.W001',
            )
        )
    return errors
