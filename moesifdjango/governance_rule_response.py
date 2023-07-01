class GovernanceRuleBlockResponse:
    def __init__(self):
        self.block_response_status = None
        self.block_response_headers = None
        self.block_response_body = None
        self.blocked = False
        self.blocked_by = None  # holds blocked by rule_id

    def update_response(self, gr_status, gr_headers, gr_body, block, rule_id):
        self.block_response_status = gr_status
        self.block_response_headers = gr_headers
        self.block_response_body = gr_body
        self.blocked = block
        self.blocked_by = rule_id

