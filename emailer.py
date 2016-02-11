import mandrill
from nameko.rpc import rpc

class Emailer(object):
    name = "emailer"

    @rpc
    def sendEmail(self,sender,recipient,text,key):
        # instanciate a new one every time to avoid possible
        # concurrency issues.
        m = mandrill.Mandrill(apikey=key)
        email = dict(
            text = text,
            subject = 'Payment received',
            from_email = sender,
            from_name = 'Claude Gibert',
            to = [ dict(email = recipient) ],
            key = key,
        )
        result = m.messages.send(email)
        return  result
