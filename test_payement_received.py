from faker import Factory
from nameko.testing.services import worker_factory
from paymentreceived import PaymentReceived
from paymentservice import PaymentService

fake = Factory.create()

class FakeEmailer(object):
    
    def sendEmail(self,sender,recipient,text,key):
        print recipient

def test_payment_service():
    service = worker_factory(PaymentReceived,emailer=FakeEmailer())

    producer = PaymentService()
    payload = producer.createData()

    service.handle_event(payload)

#test_payment_service()
