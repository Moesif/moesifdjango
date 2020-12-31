
class MaskData:

    def __init__(self):
        pass

    @classmethod
    def mask_headers(cls, headers, masks):
        """
        filters any headers (a dictionary) with key that matches those in the
        masks (a list)
        This have a side effect, so please make a deepcopy before using.
        """
        if headers is None:
            return headers
        if masks is None:
            return headers

        # Convert headers key to lowercase
        headers = {k.lower(): v for k, v in headers.items()}

        # Convert masks fields to lower case
        masks = [x.lower() for x in masks]

        for member in masks:
            headers.pop(member, None)

        return headers

    def mask_body(self, body, masks):
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
            return [self.mask_body(element, masks) for element in body]

        if type(body) == dict:
            for mask in masks:
                body.pop(mask, None)
            for key in body:
                body[key] = self.mask_body(body[key], masks)
            return body

        return body
