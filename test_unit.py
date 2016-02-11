import pytest
from faker import Factory
from nameko.testing.services import worker_factory
from paymentreceived import PaymentReceived
from paymentservice import PaymentService
from emailer import InvalidEmail,FailedSendingEmail

fake = Factory.create()
producer = PaymentService()
payload = producer.createData()

class FakeEmailer(object):
    """
        We replace the emailer with a fake emailer
        not much logic to test, we make sure the 
        templated email has the right substitutions
        by searching and counting the the values in the
        final email text.
    """

    fields = [
        ('payee','name'),
        ('payment','amount'),
        ('payment','currency'),
        ('client','name'),
        ('client','email'),
    ]
    
    def sendEmail(self,sender,recipient,text,key):
        found = 0
        for key1,key2 in self.fields:
            if text.find(str(payload[key1][key2])) != -1:
                found += 1
        assert found == len(self.fields)

class InvalidEmailer(object):
    def sendEmail(self,sender,recipient,text,key):
        raise InvalidEmail()

class FailedEmailer(object):
    def sendEmail(self,sender,recipient,text,key):
        raise FailedSendingEmail()

def test_payment_service():
    service = worker_factory(PaymentReceived,emailer=FakeEmailer())
    service.handle_event(payload)

    service = worker_factory(PaymentReceived,emailer=InvalidEmailer())
    pytest.raises(InvalidEmail,service.handle_event,payload)
    service = worker_factory(PaymentReceived,emailer=FailedEmailer())
    pytest.raises(FailedSendingEmail,service.handle_event,payload)

test_payment_service()
