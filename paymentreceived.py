import os
import yaml
from nameko.rpc import rpc
from nameko.events import EventDispatcher, event_handler
from emailer import Emailer

class PaymentReceived(object):
    name = "payment_received"

    # would normally use a library of mine
    with open(os.path.join(os.path.dirname(__file__),'config.yaml')) as f:
        config = yaml.load(f)

    emailer = Emailer()

    def createTemplateValues(self,payload):
        """ 
            keep it simple. We could flatten the payload into a
            dictionary with dot notated keys reflecting the 
            depth of the payload and use dotted notation in the
            template
        """
        replace = {}
        replace['payee'] = payload['payee']['name']
        replace['amount'] = payload['payment']['amount']
        replace['currency'] = payload['payment']['currency']
        replace['client'] = payload['client']['name']
        replace['email'] = payload['client']['email']
        return replace

    def createEmail(self,replace):
        contents = self.config['email']['template']
        for key, value in replace.items():
            contents = contents.replace('{%s}' % key,str(value))
        return contents

    @event_handler('payments','payment_received')
    def handle_event(self,payload):
        """ 
           we assume that we can trust the payload format
           if not we would need to validate it before using it
        """
        text = self.createEmail(self.createTemplateValues(payload))
        self.emailer.sendEmail(
            sender = self.config['email']['sender'],
            recipient = payload['payee']['email'],
            text = text,
            key = self.config['email']['key']
        )
