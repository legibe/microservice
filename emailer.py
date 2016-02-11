import mandrill
from nameko.extensions import DependencyProvider

__all__ = ['Emailer','InvalidEmail','FailedSendingEmail']

class InvalidEmail(Exception):
    pass

class FailedSendingEmail(Exception):
    pass

class Emailer(DependencyProvider):

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
        try:
            res = m.messages.send(email)
        except mandrill.ValidationError as e:
            raise InvalidEmail(e)
        else:
            result = res[0]
            if not result['status'] == 'sent':
                raise FailedSendingEmail('%s %s' % (result['status'],result['reject_reason']))

    def get_dependency(self, worker_ctx):
        return self
