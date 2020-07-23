from biaoqingbao import create_app

test_app = create_app()

def create_login_client(user_id=1):
    client = test_app.test_client()
    with client.session_transaction() as sess:
        sess['login'] = True
        sess['user_id'] = user_id
    return client