import os
import time
import yaml
import mandrill
from date import Date, Day, dateFromTimeStamp
from nameko.testing.utils import get_container
from nameko.testing.services import restrict_entrypoints, replace_dependencies
from nameko.testing.services import entrypoint_hook
from paymentreceived import PaymentReceived
from paymentservice import PaymentService

"""
This is a complete end-to-end test, perhaps going a bit far. It checks that the email which 
is sent to Mandrill has arrived.
"""

# need that info for Mandrill
with open(os.path.join(os.path.dirname(__file__),'config.yaml')) as f:
    config = yaml.load(f)

# retrieved the latest email reported as sent
def latest_email():
    m = mandrill.Mandrill(apikey=config['email']['key'], debug=False)
    date = Day(Date())
    result = m.messages.search(
        senders=[config['email']['sender']],
        date_from='%s' % date,
        date_to='%s' % date,
        limit = 1
    ) 
    return result[0]

def test_payment_service_received(runner_factory, rabbit_config):
    # remember when we started
    start = Date()
    # run services in the normal manner
    runner = runner_factory(rabbit_config, PaymentService, PaymentReceived)
    container = get_container(runner, PaymentService)
    runner.start()

    with entrypoint_hook(container, "emit_event") as entry_point:
        entry_point()
        # give Mandrill some time, going too fast would make the
        # test fail
        time.sleep(20)
        latest = latest_email()
        timestamp = dateFromTimeStamp(latest['ts'])
        # we success if the last email was sent in the last 20s
        assert (timestamp - start) <= 20
