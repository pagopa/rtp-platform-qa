from config.configuration import config


ACTIVATION_URL = config.activation_base_url_path + config.activation_path
ACTIVATION_URL_DEV = config.activation_base_url_path_dev + config.activation_path
ACTIVATION_LIST_URL = config.activation_base_url_path + config.activation_list_path
ACTIVATION_BY_ID_URL = config.activation_base_url_path + config.activation_by_id_path
MC_SHARED_AUTH_URL = config.mcshared_auth_url
MC_SHARED_AUTH_URL_DEV = config.mcshared_auth_url_dev
CBI_AUTH_URL = config.cbi_auth_url
CALLBACK_URL = config.callback_url
CANCEL_RTP_OPERATION = config.cancel
CANCEL_RTP_URL = config.rtp_creation_base_url_path + config.cancel_rtp_path
DEACTIVATION_URL = config.activation_base_url_path + config.deactivation_path
DEBT_POSITIONS_URL = config.debt_positions_base_url_path + config.debt_positions_path
DEBT_POSITIONS_URL_DEV = config.debt_positions_dev_base_url_path + config.debt_positions_dev_path
DEBT_POSITIONS_DELETE_URL = config.debt_positions_base_url_path + config.debt_positions_delete_path
DEBT_POSITIONS_DELETE_URL_DEV = config.debt_positions_dev_base_url_path + config.debt_positions_dev_delete_path
DEBT_POSITIONS_UPDATE_URL = config.debt_positions_base_url_path + config.debt_positions_update_path
DEBT_POSITIONS_UPDATE_URL_DEV = config.debt_positions_dev_base_url_path + config.debt_positions_dev_update_path
CREATE_RTP_OPERATION = config.cancel_rtp_operation
CBI_SEND_URL = config.cbi_send_url
POSTE_SEND_URL = config.poste_send_url
ICCREA_SEND_URL = config.iccrea_send_url
GET_RTP_URL = config.rtp_creation_base_url_path + config.get_rtp_path
GET_RTP_BY_NOTICE_NUMBER_URL = config.rtp_creation_base_url_path + config.get_rtp_by_notice_number_path
LANDING_PAGE_URL = config.landing_page_path
PAYEES_URL = config.rtp_creation_base_url_path + config.payees_registry_path
PRODUCER_GPD_MESSAGE_URL = config.producer_gpd_message_base_url + config.send_gpd_message
SEND_RTP_URL = config.rtp_creation_base_url_path + config.send_rtp_path
SERVICE_PROVIDER_MOCK_URL = config.mock_service_provider_url
SERVICE_PROVIDERS_URL = config.rtp_creation_base_url_path + config.service_providers_registry
TAKEOVER_URL = config.activation_base_url_path + config.activation_takeover
TAKEOVER_NOTIFICATION_URL = config.takeover_notification_url
LANDING_PAGE_URL = config.landing_page_path
RTP_SENDER_GPD_MESSAGE_URL = config.rtp_creation_base_url_path + config.send_gpd_message_path
