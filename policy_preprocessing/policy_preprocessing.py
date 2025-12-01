import re
from collections import defaultdict

class PolicyPreprocessor:
  
    def __init__(self, policy):
       self.invert_rules(policy)
       self.group_rules(policy)

        
        
        
        
         # ---------------------------------------------------------
         
         
    def invert_rules(self, policy):
        # Convert dict items to a list for ordering
        items = list(policy.invert_rules.items())
        # Reverse order
        items.reverse()

        i = 1
        j = len(items)
        inverted = {}
        rule_to_rule={}

        for key, value in items:
            # key = old rule id (like "R1"), value = rule text or rule dict
            rule_to_rule[f"R{j}"] = f"R{i}"
            inverted[f"R{i}"] = policy.rules[f"R{j}"]
            i += 1
            j -= 1

        # Replace with new inverted version
        policy.invert_rules = inverted
        policy.invert_rule_to_rule = rule_to_rule
    
     
        # ---------------------------------------------------------
   
    def group_rules(self,policy):
        self.extract_conditions(policy) 
     

    def extract_conditions(self, policy):
        pattern = re.compile(
            r'^(?P<decision>Grant|Deny)\s+'
            r'(?P<action>\w+)(?:\{(?P<attribute>\w+)\})?\s+'  # 🟢 supports {attribute}
            r'on\s+(?P<type>nodes|relationships)\s+'
            r'\((?P<variable>\w+):(?P<element>\w+)\)\s*'
            r'(?:where\s+(?P<condition>.+?)\s+)?'
            r'to\s+(?P<role>\w+)$',
            re.IGNORECASE
        )

        i = 1
        condition_groups = defaultdict(dict)
        condition_origin = defaultdict(dict)

        for invert_rule_id, rule in policy.invert_rules.items():
            text = rule.rstrip(';').strip()
            i += 1
            policy.invert_rules[invert_rule_id] = text
            m = pattern.match(text)
            if not m:
                print(f"Skipping invalid rule: {policy.invert_rule_to_rule[invert_rule_id]}")
                continue

            data = m.groupdict()

            # Include attribute if it exists
            action_key = data['action'].lower()
            if data['attribute']:
                action_key += f"{{{data['attribute'].lower()}}}"

            key = (
                data['decision'].lower(),
                action_key,
                data['type'].lower(),
                data['element'].lower(),
                data['role'].lower()
            )

            label = f"C{len(condition_groups[key]) + 1}"

            if data['condition']:
                condition = label + ": " + data['condition'].strip()
            else :
                condition = label + ": true"
                
            condition_groups[key][label] = condition
            condition_origin[key][label] = invert_rule_id

        # --- Format result ---
        result = {}
        origin_result = {}

        for i, (key, conds) in enumerate(condition_groups.items(), 1):
            group_name = f"group{i}"
            result[group_name] = conds
            origin_result[group_name] = condition_origin[key]

        policy.grouped_conditions = result
        policy.condition_to_rule = origin_result
