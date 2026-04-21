import sys, os

import config
sys.path.append(os.path.dirname(__file__))



class Rel_LLM():
    
    def __init__(self, llm):
        self.llm=llm
        self.prompts={}
        if (config.USE_COT):
            self.prompts["system_prompt"]=self.llm.getFileContent("prompts/relev","relev_cot.txt")
            self.prompts["json_prompt"]=self.llm.getFileContent("prompts/relev","relev_json.txt")
        else:
            #read prompt file
            self.prompts["system_prompt"]=self.llm.getFileContent("prompts/relev","relev_simple.txt")

               #inject few shots in the 1st system prompt
        if(config.USE_FEW_SHOTS):
            self.prompts["system_prompt"]+=self.llm.getFileContent("few_shots","relev_fewshots.txt")
            
        if(config.USE_VALIDATION):
            self.prompts["validation_prompt"]=self.llm.getFileContent("prompts/relev","relev_validate.txt")
   
        
        

        
    def check(self,policy):
        llm_output = self.llm.generate(self.prompts,policy,'relev',prev_output=None)        
        self.llm.repair(policy,llm_output,True)
                     

    
    
    def repair(self,policy,group,repair,grouped_conditions,operation="unsat"):
        # Loop over 'remove'

            for cond in repair:  
                explanation=repair[cond]
                
                #remove condition (so not use it in the redundancy check)
                del grouped_conditions[cond]
                
                removed_rule=policy.condition_to_rule[group][cond]
                policy.invert_rules.pop(removed_rule, None)
                original_remove_rule=policy.invert_rule_to_rule[removed_rule]
                policy.rules.pop(original_remove_rule, None)
                
                if operation=="redund":
                    print(f"Removing {original_remove_rule} {explanation}")
                else:
                    print(f"Removing {original_remove_rule} (Unsat condition: {explanation})")
                
                
        
