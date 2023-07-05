from .governance_rules import RuleType
from .governance_rule_response import GovernanceRuleBlockResponse


class BlockResponseBufferList:
    def __init__(self, rule_type=RuleType.REGEX.value):
        self.responses = []
        self.rule_type = rule_type
        self.blocked = False

    def update(self, block, updated_gr_status, updated_gr_headers, updated_gr_body, rule_id):
        if not self.rule_type:
            self.rule_type = 'regex'
        if block and not self.blocked:
            self.blocked = True

        gov_rule_response = GovernanceRuleBlockResponse()
        gov_rule_response.update_response(updated_gr_status, updated_gr_headers, updated_gr_body, block, rule_id)
        self.responses.append(gov_rule_response)
