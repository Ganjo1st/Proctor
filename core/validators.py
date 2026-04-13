import re


def validate_proxy(proxy):
    """
    Validate the given proxy.
    Proxy format: ip:port
    """
    pattern = r'^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$'
    return re.match(pattern, proxy) is not None


def normalize_proxy(proxy):
    """
    Normalize the given proxy by removing whitespace and ensuring lowercase.
    """
    return proxy.strip().lower() if validate_proxy(proxy) else None
