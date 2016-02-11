from nameko.testing.utils import get_container
from nameko.testing.services import restrict_entrypoints, replace_dependencies
from nameko.testing.services import entrypoint_hook
from paymentreceived import PaymentReceived
from paymentservice import PaymentService


"""
 the integration test consists in calling the emit_event method on the payment service
 and verify that the payment_receive service is called. To do so, we replace the
 "emailer" dependency in the payment_received service with a MagicMock instance and
 check that the sendEmail method was called on the mock object (called by the
 payment_received service).
 another possibilty of end to end testing would be to have an email sent to a test
 email address and check that an email was received.
"""
def test_payment_service_received(runner_factory, rabbit_config):
    # run services in the normal manner
    runner = runner_factory(rabbit_config, PaymentService, PaymentReceived)

    # replace the emailer with a mock instance we will check if it was called
    emailer = replace_dependencies(get_container(runner, PaymentReceived),'emailer')

    container = get_container(runner, PaymentService)
    runner.start()

    with entrypoint_hook(container, "emit_event") as entry_point:
        entry_point()
        assert emailer.sendEmail.called
