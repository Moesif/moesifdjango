class GovernanceRuleBlockResponse:
    # TODO Create a empty init, and add function
    def __init__(self):
        self.block_response_status = None
        self.block_response_headers = None
        self.block_response_body = None
        self.blocked = False

    def update_response(self, gr_status, gr_headers, gr_body, block):
        self.block_response_status = gr_status
        self.block_response_headers = gr_headers
        self.block_response_body = gr_body
        self.blocked = block
