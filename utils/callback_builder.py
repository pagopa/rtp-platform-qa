def build_callback_with_original_msg_id(generator_fn, original_msg_id: str, is_document: bool = False):
    """
    Helper to build a callback payload with the given OrgnlMsgId.
    Parameters:
    - generator_fn: function that generates the callback (e.g., generate_callback_data_DS_04b_compliant)
    - original_msg_id: value to set in OrgnlMsgId
    - is_document: True if the path includes 'Document' (DS_08N / DS_05_ACTC)
    """
    callback_data = generator_fn()
    root = callback_data['AsynchronousSepaRequestToPayResponse']
    if is_document:
        root = root['Document']

    root['CdtrPmtActvtnReqStsRpt']['OrgnlGrpInfAndSts']['OrgnlMsgId'] = original_msg_id
    return callback_data


def build_rfc_callback_with_original_msg_id(generator_fn, original_msg_id: str):
    """
    Helper to build an RFC callback payload with the given OrgnlMsgId.
    
    This is specifically for DS12P/DS12N callbacks using the
    SepaRequestToPayCancellationResponse structure.
    
    Parameters:
    - generator_fn: function that generates the RFC callback 
                   (e.g., generate_callback_data_DS_12P_CNCL_compliant)
    - original_msg_id: value to set in OrgnlMsgId (the ID of the original RTP)
    """
    callback_data = generator_fn()
    
    rfc_root = callback_data['SepaRequestToPayCancellationResponse']['Document']['RsltnOfInvstgtn']
    
    rfc_root['Assgnmt']['Id'] = original_msg_id
    
    rfc_root['CxlDtls'][0]['TxInfAndSts'][0]['OrgnlGrpInf']['OrgnlMsgId'] = original_msg_id
    
    return callback_data
