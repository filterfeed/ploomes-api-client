from requests import Session

class SessionManager:
    def __init__(self, headers):
        self.session = Session()
        self.session.headers.update(headers)
        # Additional customization can go here
