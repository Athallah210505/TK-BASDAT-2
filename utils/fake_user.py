class FakeUser:
    def __init__(self, username, role):
        self.username = username
        self.role = role
        self.is_authenticated = True

    def get_username(self):
        return self.username
