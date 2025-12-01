import sys, os
sys.path.append(os.path.dirname(__file__))



class Astonishment_LLM():
    
    def __init__(self, llm):
        self.llm=llm
   
        
        

        
    def check(self,policy):
        #read prompt file
        system_prompt=self.llm.getFileContent("prompts","prompt4_astonishment.txt")
        #inject few shots in the prompt
        system_prompt+=self.llm.getFileContent("few_shots","few_shots4_astonishment.txt")
       # print(system_prompt)
        
        
        llm_input = [f"{key}: {value}" for key, value in policy.invert_rules.items()]
        
        llm_output = self.llm.generate(system_prompt,llm_input)
 
        
        if("remove" in llm_output):
            self.repair(policy,llm_output["remove"])


       

    
    
    def repair(self,policy,repair):
        # Loop over 'remove'
   

        for removed_rule in repair:  
            explanation=repair[removed_rule]
            policy.invert_rules.pop(removed_rule, None)
                
            original_remove_rule=policy.invert_rule_to_rule[removed_rule]
            policy.rules.pop(original_remove_rule, None)
            print(f"Removing {original_remove_rule} ({explanation})")
        

        
        
