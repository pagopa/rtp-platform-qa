def extract_next_activation_id(res):
    """
    Extracts the 'nextActivationId' from the response object.
    - first checks the body (metadata or page)
    - then checks the top-level of the body
    - finally checks the header 'NextActivationId'
    """
    body = res.json()
    for key in ('metadata', 'page'):
        meta = body.get(key)
        if isinstance(meta, dict) and meta.get('nextActivationId'):
            return meta['nextActivationId']
    if isinstance(body, dict) and body.get('nextActivationId'):
        return body['nextActivationId']
    return res.headers.get('NextActivationId')
