SECRET_KEY = "Mcc+ugWtku6TD+KrBPT5tTIWSQD6HRFuQeVKJmWKhGAok6BmSDAaYcOb"
TALISMAN_ENABLED = False
# Добавление русского языка в список доступных языков
LANGUAGES = {
    "ru": {"flag": "ru", "name": "Русский"},
    "en": {"flag": "us", "name": "English"},
}
BABEL_DEFAULT_LOCALE = "ru"
FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    "DATAPANEL_CLOSED_BY_DEFAULT": True,
    "DASHBOARD_VIRTUALIZATION": True,
    "DASHBOARD_RBAC": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ESCAPE_MARKDOWN_HTML": False,
    "LISTVIEWS_DEFAULT_CARD_VIEW": True,
    "THUMBNAILS": True,
    "DRILL_BY": True,
    "DRILL_TO_DETAIL": True,
    "HORIZONTAL_FILTER_BAR": True,
    "ESTIMATE_QUERY_COST": True,
    "TAGGING_SYSTEM": True,
    "HTML_SANITIZATION": False,
    "TALISMAN_ENABLED": False,
    "CONTENT_SECURITY_POLICY": None,
}

# WEBDRIVER_BASEURL="http://superset:8088/superset"
# ENABLE_PROXY_FIX = True
# SUPERSET_WEB_SERVER_PORT = 8088
# STATIC_ASSETS_PREFIX = "/superset"
# APPLICATION_ROOT = "/superset"
WTF_CSRF_ENABLED = False
WTF_CSRF_SECRET_KEY = " KhGAok6BmSDAaYcOb"
HTML_SANITIZATION = False
TALISMAN_ENABLED = False
CONTENT_SECURITY_POLICY = None
