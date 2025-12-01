import config
import requests
import sys, os
import copy
sys.path.append(os.path.dirname(__file__))



class LLM_Model:
    
    def __init__(self, model_name,input_policy):
        self.model_name = model_name
        self.input_policy=input_policy
        
        
    
    def anomaly_checking(self,policy,anomaly_type):
        
        try:
            repaired_policy = copy.deepcopy(policy)
            anomaly_type.check(repaired_policy)
            
        except Exception as exc:   
            print(f"Error during anomaly checking: {exc}")
            
        return repaired_policy
        
        
    
    def list_to_text(self,input):
        return "\n".join(input)
    
    
 
    def generate(self,system_prompt,input, retry=0):
        import json,re,time
        
        input=self.list_to_text(input)
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input}
            ],
            "temperature": 0,
            "top_p": 1,
            "seed": 0, 
            "max_tokens": 10000,
        }

        response = requests.post(config.API_URL, headers=config.HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()
       
        if "choices" in data:
            output_text=data["choices"][0]["message"]["content"].strip()
        elif "output" in data:
            output_text=data["output"]
        elif "response" in data:
            output_text=data["response"]
        else:
            raise ValueError("Unhandled LLM response format: " + str(data))
        # Clean out ```json or ``` wrappers
        
        
  
        output_text = re.sub(r"^```(?:json)?|```$", "", output_text, flags=re.MULTILINE).strip()
        
    
       
       
        if(output_text==""):
            output_text='{}'
        output={}
        
        try:
            return json.loads(output_text)
        except json.JSONDecodeError as e:
            # Try to fix only the specific case you mentioned
            if "Expecting ',' delimiter" in str(e):
                # Try adding a closing brace
                fixed = output_text.strip()
                if not fixed.endswith("}"):
                    fixed = fixed + "}"
                try:
                    return json.loads(fixed)
                except:
                    pass  # fallback below
        
        return output
 
     # ======================================================
    # ---------------- Read File Helper --------------------
    # ======================================================
    def getFileContent(self,type, file_name):
        import os
        base_dir = os.path.dirname(__file__)
        file_path = os.path.join(base_dir, "..", type, file_name)
        file_path = os.path.abspath(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()