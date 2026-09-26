import pytest
from src.contact_form import ContactForm


def test_contact_form_valid_submission():
    form = ContactForm('John', 'Doe', 'john.doe@example.com', 'Hello!')
    assert form.is_valid() is True


def test_contact_form_missing_first_name():
    form = ContactForm('', 'Doe', 'john.doe@example.com', 'Hello!')
    assert form.is_valid() is False


def test_contact_form_invalid_email():
    form = ContactForm('John', 'Doe', 'john.doe', 'Hello!')
    assert form.is_valid() is False


def test_contact_form_database_failure():
    form = ContactForm('John', 'Doe', 'john.doe@example.com', 'Hello!')
    form.save_to_db = lambda: (_ for _ in ()).throw(Exception('DB Error'))
    with pytest.raises(RuntimeError, match='Database error occurred'):
        form.submit()
