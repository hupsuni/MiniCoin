
class NoNonceException(ValueError):

    def __init__(self, message=None):
        self.strerror = message
        if message is None:
            self.strerror = "No nonce provided, cannot hash block!"
