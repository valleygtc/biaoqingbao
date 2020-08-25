from biaoqingbao import create_app, generate_token

test_app = create_app()

def create_login_client(user_id=1):
    client = test_app.test_client()
    token = generate_token({ 'user_id': user_id })
    client.set_cookie('localhost', 'token', token)
    client.cookie_jar
    return client

def get_cookies(client):
    # http.cookiejar.CookieJar
    # http.cookiejar.Cookie
    return {
        cookie.name: cookie for cookie in client.cookie_jar
    }
