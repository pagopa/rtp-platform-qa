import uuid

from .datetime_utils import generate_create_time
from .datetime_utils import generate_future_time

from .generators_utils import generate_random_string


def generate_callback_data_DS_04b_compliant(BIC: str = 'MOCKSP04') -> dict:
    """Generate DS-04b compliant callback data.

    Args:
        BIC: Bank Identifier Code

    Returns:
        Dictionary containing DS-04b compliant callback data
    """
    message_id = str(uuid.uuid4())
    resource_id = f"TestRtpMessage{generate_random_string(16)}"
    original_msg_id = f"TestRtpMessage{generate_random_string(20)}"

    create_time = generate_create_time()
    original_time = generate_future_time(1)

    return {
        'resourceId': resource_id,
        'AsynchronousSepaRequestToPayResponse': {
            'CdtrPmtActvtnReqStsRpt': {
                'GrpHdr': {
                    'MsgId': message_id,
                    'CreDtTm': create_time,
                    'InitgPty': {'Id': {'OrgId': {'AnyBIC': BIC}}},
                },
                'OrgnlGrpInfAndSts': {
                    'OrgnlMsgId': original_msg_id,
                    'OrgnlMsgNmId': 'pain.013.001.08',
                    'OrgnlCreDtTm': original_time,
                },
                'OrgnlPmtInfAndSts': [{'TxInfAndSts': {'TxSts': ['RJCT']}}],
            }
        },
        '_links': {
            'initialSepaRequestToPayUri': {
                'href': f"https://api-rtp-cb.uat.cstar.pagopa.it/rtp/cb/requests/{resource_id}",
                'templated': False,
            }
        },
    }