from faker import Factory

from nameko.events import EventDispatcher
from nameko.timer import timer

fake = Factory.create()

class PaymentService(object):
    name = "payment_service"

    dispatch = EventDispatcher()

    def createData(self):
        return {
            'client': {
                'name': fake.name(),
                'email': fake.safe_email()
            },
            'payee': {
                'name': fake.name(),
                'email': fake.safe_email()
            },
            'payment': {
                'amount': fake.random_int(),
                'currency': fake.random_element(
                    ("USD", "GBP", "EUR")
                )
            }
        }

    @timer(interval=10)
    def emit_event(self):
        payload = self.createData()
        self.dispatch("payment_received", payload)
