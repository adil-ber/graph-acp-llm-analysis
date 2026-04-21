import json
import sys, os
import config

sys.path.append(os.path.dirname(__file__))



class Astonishment_LLM():
    
    def __init__(self, llm):
        self.llm=llm
        self.prompts={}
        
        if (config.USE_COT):
            self.prompts["system_prompt"]=self.llm.getFileContent("prompts/la","pola_cot.txt")
            self.prompts["json_prompt"]=self.llm.getFileContent("prompts/la","pola_json.txt")
            
        else:
            #read prompt file
            self.prompts["system_prompt"]=self.llm.getFileContent("prompts/la","pola_simple.txt")
        
        
        #inject few shots in the 1st system prompt
        if(config.USE_FEW_SHOTS):
            self.prompts["system_prompt"]+=self.llm.getFileContent("few_shots","la_fewshots.txt")
        
        if(config.USE_VALIDATION):
            self.prompts["validation_prompt"]=self.llm.getFileContent("prompts/la","pola_validate.txt")
   
        
        

        
    def check(self,policy):
        llm_output = self.llm.generate(self.prompts,policy,'la',prev_output=None)        
        self.llm.repair(policy,llm_output,True)


    # not usedd now
    def repair(self,policy,repair,final_repair=False):
        
        if "to add" not in repair and "to remove" not in repair:
            print("No repair instructions found.")
            return
                
        if "to remove" in repair: 
            # Loop over 'remove'
            to_remove=repair["to remove"]
            for removed_rule in to_remove:  
                explanation=to_remove[removed_rule]
                policy.invert_rules.pop(removed_rule, None)
                
                if config.USE_INVERTED_RULES:    
                    original_remove_rule=policy.invert_rule_to_rule[removed_rule]
                else :
                    original_remove_rule=removed_rule
                    
                policy.rules.pop(original_remove_rule, None)
                if final_repair:
                    print(f"Removing {original_remove_rule} ({explanation})")
                
                
        # Loop over 'add'
        if "to add" in repair:
            if final_repair:
                for new_rule_id,new_rule in repair['to add'].items():  
                    print(f"Adding {new_rule_id}: {new_rule}")
                
            policy.invert_rules.update(repair['to add'])
            policy.rules.update(repair['to add'])
       

        
