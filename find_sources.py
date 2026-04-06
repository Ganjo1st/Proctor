# В начале файла добавьте:
from core.proxy_rotator import ProxyRotator

# В функции verify_source замените код на:
async def verify_source(url: str, source_type: str, db) -> bool:
    """Проверка работоспособности источника с ротацией прокси"""
    rotator = ProxyRotator(db)
    headers = {'User-Agent': UserAgent().random}
    
    html, used_proxy = await rotator.fetch_with_proxy_rotation(url, headers)
    
    if html:
        # Проверяем наличие прокси
        pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}:[0-9]{2,5}\b'
        if re.search(pattern, html):
            return True
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, html)
        if len(ips) > 5:
            return True
    return False
