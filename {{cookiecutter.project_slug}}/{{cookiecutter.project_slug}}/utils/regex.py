try:
    import re2 as re
except ImportError:
    import re
else:
    re.set_fallback_notification(re.FALLBACK_WARNING)
