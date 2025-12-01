import sys, os
sys.path.append(os.path.dirname(__file__))
from policy_preprocessing.policy_preprocessing import PolicyPreprocessor
from collections import defaultdict
import csv

class Policy:
  
    def __init__(self, policy_id,type, property_checked=None):
        self.policy_id=policy_id
        
        if(type=="expected"):        
            self.rules = self.load_rules(f"policy_sets/{type}_policies/{property_checked}",f"{policy_id}.csv")

        if(type=="input"):
            self.rules = self.load_rules(f"policy_sets/{type}_policies",f"{policy_id}.csv")
            self.invert_rules = self.rules.copy()
            self.invert_rule_to_rule = defaultdict(dict)
            self.grouped_conditions = defaultdict(dict)
            self.condition_to_rule = defaultdict(dict)
            
            self.preprocessor = PolicyPreprocessor(self)



    def load_rules(self,type,file_path):
        rules = {}  # use a dict, not a list

        base_dir = os.path.dirname(__file__)
        full_path = os.path.join(base_dir,"..",f"{type}", file_path)

        with open(full_path, mode="r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # skip header if present

            for row in reader:
                if len(row) < 2:
                    continue  # skip invalid rows

                rule_id, rule_text = row[0].strip(), row[1].strip()
                rules[rule_id] = rule_text  # ✅ directly store as key:value

        return rules



    def read_rules_from_csv(self,file_path):
        rules = []
        
        base_dir = os.path.dirname(__file__)
        full_path = os.path.join(base_dir, file_path)

        with open(full_path, mode="r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # skip header if present         
            for row in reader:
                if len(row) < 2:
                    continue  # skip invalid rows
                rule_id, rule_text = row[0].strip(), row[1].strip()
                             
                #rules.append({"rule_id": rule_id, "rule_text": rule_text})
                rules.append({f"{rule_id}":f"{rule_text}"})

            return rules

    # ---------------------------------------------------------

    def policy_export(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(base_dir, "..", "policy_sets", "repaired_policies")
        output_dir = os.path.abspath(output_dir)
        
        output_path = os.path.join(output_dir, f"repaired_{self.policy_id}.csv")

        with open(output_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(["rule_id", "rule_text"])
            
            
            for rule_id, rule in self.rules.items():
                writer.writerow([rule_id, rule])

        print(f"✅ Rules written to {output_path}")