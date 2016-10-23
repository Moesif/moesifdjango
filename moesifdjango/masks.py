

def mask_headers(headers, masks):
    """
    filters any headers (a dictionary) with key that matches those in the
    masks (a list)
    This have a sideeffect, so please make a deepcopy before using.
    """
    if headers is None:
        return headers
    if masks is None:
        return headers

    for member in masks:
        headers.pop(member, None)

    return headers


def mask_body(body, masks):
    """
    recursively removes any element from body (dictionary or lists) that
    have key matches masks. Note, this function have a side effect.
    Please make a deepcopy before using.
    """
    if body is None:
        return body
    if masks is None:
        return body

    if type(body) == list:
        return [mask_body(element, masks) for element in body]

    if type(body) == dict:
        for mask in masks:
            body.pop(mask, None)
        for key in body:
            body[key] = mask_body(body[key], masks)
        return body

    return body
