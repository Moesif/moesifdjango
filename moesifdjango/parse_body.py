import gzip
from .masks import MaskData
import json
import base64
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


class ParseBody:

    def __init__(self):
        self.mask_helper = MaskData()

    @classmethod
    def start_with_json(cls, body):
        return body.startswith("{") or body.startswith("[")

    @classmethod
    def transform_headers(cls, headers):
        return {k.lower(): v for k, v in headers.items()}

    @classmethod
    def base64_body(self, body):
        return base64.standard_b64encode(body).decode(encoding="UTF-8"), "base64"

    def parse_bytes_body(self, body, headers, body_masks):
        try:
            if (headers is not None and "content-encoding" in headers and headers["content-encoding"] is not None
                    and "gzip" in (headers["content-encoding"]).lower()):
                parsed_body, transfer_encoding = self.base64_body(gzip.decompress(body))
            else:
                string_data = body.decode(encoding="UTF-8")
                if self.start_with_json(string_data):
                    parsed_body = json.loads(string_data)
                    parsed_body = self.mask_helper.mask_body(parsed_body, body_masks)
                    transfer_encoding = 'json'
                else:
                    parsed_body, transfer_encoding = self.base64_body(body)
        except:
            parsed_body, transfer_encoding = self.base64_body(body)
        return parsed_body, transfer_encoding

    def parse_string_body(self, body, headers, body_masks):
        try:
            if self.start_with_json(body):
                parsed_body = json.loads(body)
                parsed_body = self.mask_helper.mask_body(parsed_body, body_masks)
                transfer_encoding = 'json'
            elif (headers is not None and "content-encoding" in headers and headers["content-encoding"] is not None
                  and "gzip" in (headers["content-encoding"]).lower()):
                decompressed_body = gzip.GzipFile(fileobj=StringIO(body)).read()
                parsed_body, transfer_encoding = self.base64_body(decompressed_body)
            else:
                parsed_body, transfer_encoding = self.base64_body(body)
        except:
            parsed_body, transfer_encoding = self.base64_body(body)
        return parsed_body, transfer_encoding
