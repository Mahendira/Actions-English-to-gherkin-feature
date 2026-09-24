class ContactForm:
    def __init__(self, first_name, last_name, email, message):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.message = message

    def is_valid(self):
        return (self.first_name and self.last_name and self.is_valid_email() and self.message)

    def is_valid_email(self):
        # Simple email validation
        return '@' in self.email and '.' in self.email.split('@')[-1]

    def save_to_db(self):
        # Placeholder for saving to DynamoDB
        pass

    def submit(self):
        if not self.is_valid():
            raise ValueError('Invalid form submission')
        try:
            self.save_to_db()
        except Exception:
            raise RuntimeError('Database error occurred')
