import sys, os
sys.path.append(os.path.dirname(__file__))



class Consistency_LLM():
    
    def __init__(self, llm):
        self.llm=llm
   
        
        

        
    def check(self,policy):
        #read prompt file
        system_prompt=self.llm.getFileContent("prompts","prompt3_consistency.txt")
        #inject few shots in the prompt
        system_prompt+=self.llm.getFileContent("few_shots","few_shots3_consistency.txt")


     
        llm_input = [f"{key}: {value}" for key, value in policy.invert_rules.items()]
        
        llm_output = self.llm.generate(system_prompt,llm_input)
    
        if("remove" in llm_output):
            self.repair(policy,{"remove":llm_output["remove"]})
        if("add" in llm_output):
            self.repair(policy,{"add":llm_output["add"]})
        
   
       

    
    
    def repair(self,policy,repair):
        # Loop over 'remove'
        if 'remove' in repair:
            for removed_rule in repair['remove']:  
                policy.invert_rules.pop(removed_rule, None)
                explanation=repair['remove'][removed_rule]
                original_remove_rule=policy.invert_rule_to_rule[removed_rule]
                policy.rules.pop(original_remove_rule, None)
                print(f"Removing {original_remove_rule} ({explanation})")
                
        # Loop over 'add' (only if exists)
        if 'add' in repair:
            for new_rule_id,new_rule in repair['add'].items():  
                print(f"Adding {new_rule_id}: {new_rule}")
                
            policy.invert_rules.update(repair['add'])
            policy.rules.update(repair['add'])
        
       
        
        
     