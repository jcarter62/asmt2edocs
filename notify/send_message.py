

class SendMessage:

    def __init__(self, email_address, message):
        self.message = message
        self.email_address = email_address
        

    def send(self):
        # Simulate sending a message
        print(f"Message sent: {self.message}")

    