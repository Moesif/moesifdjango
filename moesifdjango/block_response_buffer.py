from .governance_rule_response import GovernanceRuleBlockResponse


class BlockResponseBufferList:
    def __init__(self):
        self.responses = []
        self.rule_type = None
        self.blocked = False
        self.blocked_by = None  # holds blocked by rule_id

    def update(self, block, updated_gr_status, updated_gr_headers, updated_gr_body, rule_id):
        if not self.rule_type:
            self.rule_type = 'regex'
        if block and not self.blocked:
            self.blocked = True
        if self.blocked:
            self.blocked_by = rule_id

        gov_rule_response = GovernanceRuleBlockResponse()
        gov_rule_response.update_response(updated_gr_status, updated_gr_headers, updated_gr_body, block, rule_id)
        self.responses.append(gov_rule_response)
