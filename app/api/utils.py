from slowapi.util import get_remote_address

async def login_key_func(request):
    try:
        body = await request.json()
        return body.get("username", get_remote_address(request))
    except Exception:
        return get_remote_address(request)

async def register_key_func(request):
    try:
        body = await request.json()
        return body.get("username", get_remote_address(request))
    except Exception:
        return get_remote_address(request)