import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_model = None
_configured = False


class GeminiUnavailable(RuntimeError):
    pass


def get_model():
    global _model, _configured
    if _model is not None:
        return _model

    api_key = getattr(settings, 'GEMINI_API_KEY', '') or ''
    if not api_key:
        raise GeminiUnavailable("GEMINI_API_KEY is not set in the environment.")

    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise GeminiUnavailable("google-generativeai package is not installed.") from exc

    if not _configured:
        genai.configure(api_key=api_key)
        _configured = True

    _model = genai.GenerativeModel('gemini-2.0-flash')
    return _model


def generate(prompt, **kwargs):
    model = get_model()
    response = model.generate_content(prompt, **kwargs)
    return (response.text or '').strip()
