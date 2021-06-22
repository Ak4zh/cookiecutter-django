from django.conf import settings


def settings_context(_request):
    """Settings available by default to the templates context."""
    # Note: we intentionally do NOT expose the entire settings
    # to prevent accidental leaking of sensitive information
    return {
        "DEBUG": settings.DEBUG,
        "PROJECT_NAME": settings.PROJECT_NAME,
        "AUTHOR_NAME": settings.AUTHOR_NAME,
        "META_KEYWORDS": settings.META_KEYWORDS,
        "SIDEBAR_LINKS": settings.SIDEBAR_LINKS
    }
