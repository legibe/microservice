import os
import yaml
from nameko.events import EventDispatcher, event_handler
from emailer import *

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

    @event_handler('payment_service','payment_received')
    def handle_event(self,payload):
        """ 
           we assume that we can trust the payload format
           if not we would need to validate it before using it
        """
        text = self.createEmail(self.createTemplateValues(payload))
        try:
            self.emailer.sendEmail(
                sender = self.config['email']['sender'],
                recipient = payload['payee']['email'],
                text = text,
                key = self.config['email']['key']
            )
        except InvalidEmail as e:
            # bad email address, input problem?
            # need to log this and/or notify a metric system and/or admin
            # re-raise for test, nameko catches it
            raise
        except FailedSendingEmail as e:
            # the sender provided uses pub-sub.
            # sending email could fail for different reasons
            # a proper retry strategy could invold a persistent queue
            # with a worker dedicated to re-trying with a maximum number 
            # of retries. The number of failed emails and the size of 
            # the persistent queue could be used as metrics showing
            # the health of the email system.
            # a simple solution would be to use a queue in memory a class
            # level and a method called on timer to retry.
            # re-raise for test, nameko catches it
            raise
