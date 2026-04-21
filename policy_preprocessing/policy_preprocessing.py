import re
from collections import defaultdict
import sys

import config

class PolicyPreprocessor:
  
    def __init__(self, policy):
       if config.USE_INVERTED_RULES:
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
    def acr_groups_to_string(self,grouped_rules):
        """
        Convert a dict / defaultdict of lists into a readable string
        """
        lines = []

        for group_key, rules in grouped_rules.items():
            lines.append(f"{group_key}:")
            for rule in rules:
                lines.append(f"  - {rule}")
            lines.append("")  # blank line between groups

        return "\n".join(lines)
    
    
    
            # ---------------------------------------------------------
    def condition_groups_to_string(self,grouped_conditions):
        """
        Convert a dict / defaultdict of lists into a readable string
        """
        lines = []

        for group_key, conditions in grouped_conditions.items():
            lines.append(f"{group_key}:")
            for label, condition in conditions.items():
                lines.append(f"  - {label}: {condition}")
            lines.append("")  # blank line between groups

        return "\n".join(lines)
    
    
    

    def group_rules(self,policy):
        self.extract_conditions(policy) 
     

    def extract_conditions(self, policy):
        acr_groups = defaultdict(list)
        elements_groups = defaultdict(list)
        wildcard_rules=defaultdict(list)

        
        pattern = re.compile(
            r'^(?P<decision>Grant|Deny)\s+'
            r'(?P<action>\w+)(?:\{(?P<attribute>\*|\w+)\})?\s+'  # 🟢 supports {attribute}
            r'on\s+(?P<type>nodes|relationships)\s+'
            r'\((?:(?P<variable>\w+):(?P<element>\w+)|\*)\)\s*'
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
                print(f"Skipping invalid rule: {text}")
                continue

            data = m.groupdict()

            # Include attribute if it exists
            action_key = data['action'].lower()
            if data['attribute']:
                action_key += f"{{{data['attribute'].lower()}}}"

             # 🔑 attribute presence only (not name)
            has_attribute = data['attribute'] is not None
            
            if data['element'] is None:
                data['element'] = '*'
                data['variable'] = '*'

            
            key = (
                data['type'].lower(),
                data['element'] if data['element']=="*" else data['element'].lower(),
                data['role'].lower(),
                "Attribute-level" if has_attribute else "Element-level"
            )
            
            if data['element']=="*":
                wildcard_rules[key].append(invert_rule_id+"- "+text)
            
            else:
                acr_groups[key].append(invert_rule_id+"- "+text)
                
                
            element_group_key = (
                data['type'].lower(),
                data['element'] if data['element']=="*" else data['element'].lower(),
                data['role'].lower()
            )
            elements_groups[element_group_key].append(invert_rule_id+"- "+text)
    
    
    
    
            #conditions groups
            cond_key = (
                data['decision'].lower(),
                data['action'].lower(),
                data['type'].lower(),
                data['element'] if data['element']=="*" else data['element'].lower(),
                data['role'].lower(),
                "Attribute-level" if has_attribute else "Element-level"
            )
            
            label = f"C{len(condition_groups[cond_key]) + 1}"

            if data['condition']:
                condition = label + ": " + data['condition'].strip()
            else :
                condition = label + ": true"
                
            condition_groups[cond_key][invert_rule_id] = condition
            condition_origin[cond_key][invert_rule_id] = invert_rule_id

        
        
        #----- wildcard * treatment **
        for (w_type, w_element, w_role, w_level), rules in wildcard_rules.items():
            # only wildcard groups
            if w_element != '*':
                continue
            
                """       exists = self.acr_group_exists(
                    acr_groups,
                    data['type'].lower(),
                    role=data['role'].lower(),
                    level="Attribute-level" if has_attribute else "Element-level"
                )
                if exists:
                    print("A matching group exists (any element)")"""
                    
            # check if compatible groups exist
            if not self.acr_group_exists(acr_groups, w_type, w_role, w_level):
                acr_groups[(w_type, '*', w_role, w_level)] = wildcard_rules[(w_type, '*', w_role, w_level)]  # create new group
                continue
            
            #group by element
            if not self.elements_group_exists(elements_groups, w_type, w_role):
                elements_groups[(w_type, '*', w_role)] = wildcard_rules[(w_type, '*', w_role)]  # create new group
                continue
            
                # inject rules into matching concrete groups
                
            for (g_type, g_element, g_role, g_level), g_rules in acr_groups.items():
                if (
                    g_type == w_type
                    and g_role == w_role
                    and g_level == w_level
                    and g_element != '*'   # concrete only
                ):
                    for r in rules:
                        if r not in g_rules:   # avoid duplicates
                            g_rules.append(r)
                            
            for (g_type, g_element, g_role), g_rules in elements_groups.items():
                if (
                    g_type == w_type
                    and g_role == w_role
                    and g_element != '*'   # concrete only
                ):
                    for r in rules:
                        if r not in g_rules:   # avoid duplicates
                            g_rules.append(r)
        
        
        
        
        # --- Format result ---
        result = {}
        origin_result = {}

        for i, (cond_key, conds) in enumerate(condition_groups.items(), 1):
            result[cond_key] = conds
            origin_result[cond_key] = condition_origin[cond_key]




        policy.grouped_conditions = result
        policy.condition_to_rule = origin_result
        
       
        policy.grouped_rules = acr_groups
        policy.grouped_elements = elements_groups

        
        
        
    def acr_group_exists(self,acr_groups, type_, role, level):
        for (g_type, g_element, g_role, g_level) in acr_groups.keys():
            if (
                g_type == type_
                and g_role == role
                and g_level == level
            ):
                return True
        return False
    
    def elements_group_exists(self,element_groups, type_, role):
        for (g_type, g_element, g_role) in element_groups.keys():
            if (
                g_type == type_
                and g_role == role
            ):
                return True
        return False

        
