import sys, os
sys.path.append(os.path.dirname(__file__))



class Rel_LLM():
    
    def __init__(self, llm):
        self.llm=llm
   
        
        

        
    def check(self,policy):
        #read prompt file
        system_prompt_sat=self.llm.getFileContent("prompts","prompt1_satisfiability.txt")
        #inject few shots in the prompt
        system_prompt_sat+=self.llm.getFileContent("few_shots","few_shots1_satisfiability.txt")
        
          #read prompt file
        system_prompt_redund=self.llm.getFileContent("prompts","prompt2_redundancy.txt")
        #inject few shots in the prompt
        system_prompt_redund+=self.llm.getFileContent("few_shots","few_shots2_redundancy.txt")
        
        for group, conds in policy.grouped_conditions.items():
            group_conditions=conds
            
            llm_input = list(group_conditions.values())
            if(len(llm_input) != 0):
                try:      
                    #find unsat conditions
                    llm_output = self.llm.generate(system_prompt_sat,llm_input)
                    #repair unsat conditions
                    self.repair(policy,group,llm_output,group_conditions,"sat")
                
                except Exception as exc:
                    print(f"Error during satisfiability checking: {exc}")
                
                if(len(group_conditions) !=0):
                    try:
                        llm_input = list(group_conditions.values())
                        #find redundant conditions
                        llm_output = self.llm.generate(system_prompt_redund,llm_input)
                        #repair redundant conditions
                        self.repair(policy,group,llm_output,group_conditions,"redund")
                        
                    except Exception as exc:
                        print(f"Error during redundancy checking: {exc}")
                     

    
    
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
                
                
        
