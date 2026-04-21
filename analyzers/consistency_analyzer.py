import sys, os

import config
sys.path.append(os.path.dirname(__file__))



class Consistency_LLM():
    
    def __init__(self, llm):
        self.llm=llm
        self.prompts={}
        if (config.USE_COT):
            self.prompts["system_prompt"]=self.llm.getFileContent("prompts/consist","consist_cot.txt")
            self.prompts["json_prompt"]=self.llm.getFileContent("prompts/consist","consist_json.txt")    
        else:
            #read prompt file
            self.prompts["system_prompt"]=self.llm.getFileContent("prompts/consist","consist_simple.txt")
   
        if(config.USE_FEW_SHOTS):
            self.prompts["system_prompt"]+=self.llm.getFileContent("few_shots","consist_fewshots.txt") 
            
        if(config.USE_VALIDATION):
            self.prompts["validation_prompt"]=self.llm.getFileContent("prompts/consist","consist_validate.txt")
        

        
    def check(self,policy):
        llm_output = self.llm.generate(self.prompts,policy,'consist',prev_output=None)        
        self.llm.repair(policy,llm_output,True)