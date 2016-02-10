from nameko.testing.services import worker_factory
from conversionservice import ConversionService

def test_conversion_service():
    # create worker with mock dependencies
    service = worker_factory(ConversionService)

    # add side effects to the mock proxy to the "maths" service
    service.maths_rpc.multiply.side_effect = lambda x, y: x * y
    service.maths_rpc.divide.side_effect = lambda x, y: x / y

    # test inches_to_cm business logic
    assert service.inches_to_cm(300) == 762
    service.maths_rpc.multiply.assert_called_once_with(300, 2.54)

    # test cms_to_inches business logic
    assert service.cms_to_inches(762) == 300
    service.maths_rpc.divide.assert_called_once_with(762, 2.54)
