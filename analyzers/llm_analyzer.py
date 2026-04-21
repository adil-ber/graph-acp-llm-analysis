import json
import re
from urllib import response
import config
import requests
import sys, os
import copy

sys.path.append(os.path.dirname(__file__))



class LLM_Model:

    def __init__(self, model_name):
        self.model_name = model_name
        self.validation_count = 0
    
    # ======================================================
    # ---------------- LLM API TEST--------------------
    # ======================================================
    def llm_api_check(self):
        try:
            self.llm_call("API Check", "test")
        except Exception as e:
            print("API check failed:", e)
            sys.exit(1)  # exit program  
        
        
        
    # ======================================================
    # ---------------- LLM API CALL--------------------
    # ======================================================
    
    def llm_call(self,system_prompt,input):
        if config.USED_API == "mistral":
            api_key=config.MISTRAL_API_KEY
            return self.mistral_call(system_prompt,input,None,api_key)
        
        if config.USED_API == "openai":
            api_url=config.OPENAI_REASONING_API_URL
            api_key=config.OPENAI_API_KEY
            return self.openai_response_call(system_prompt,input,api_url,api_key)
        
       
        api_url=config.OPENROUTER_API_URL
        api_key=config.OPENROUTER_API_KEY
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input}
            ],
            "temperature": config.TEMPERATURE,
            "top_p": 1,
            "seed": 0, 
            "max_tokens": config.MAX_TOKENS,
            
        }
        try:
            response = requests.post(api_url, headers=headers, json=payload)
            print(response.status_code)
            #print(response.text)
            response.raise_for_status()         
            data = response.json()
        except requests.exceptions.HTTPError as e:
            print("HTTP Error:", e)
            print("Status code:", response.status_code)
            print("Response body:", response.text)

        
        if "choices" in data:
            content = data["choices"][0]["message"].get("content")
            if content is not None:
                output_text = content.strip()
            else:
                output_text = ""
                
        elif "output" in data:
            output_text=data["output"]
        elif "response" in data:
            output_text=data["response"]
        else:
            raise ValueError("Unhandled LLM response format: " + str(data))

      #  print("LLM RResponse... "f"{output_text}")
        return output_text
      
      
      
    def openai_response_call(self, system_prompt, input,api_url,api_key):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        print("URL:", api_url)
        print("HEADERS:", headers)
        payload = {
            "model": self.model_name,  # e.g. "o3-mini" or "gpt-4.1-mini"
            "input": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": input
                }
            ],
            #"temperature": config.TEMPERATURE,
            "max_output_tokens": config.MAX_TOKENS
        }

        response = requests.post(api_url, headers=headers, json=payload)
        #print(response.status_code)
        #print(response.text)
        response.raise_for_status()
        data = response.json()

        if "choices" in data:  # chat/completions
            output_text = data["choices"][0]["message"]["content"].strip()

        elif "output" in data:
            output_text = None

            for item in data["output"]:
                if item.get("type") == "message":
                    for content in item.get("content", []):
                        if content.get("type") == "output_text":
                            output_text = content.get("text", "").strip()
                            break

            if output_text is None:
                raise ValueError("No output_text found in response.")

        else:
            raise ValueError(f"Unhandled LLM response format: {data}")

        #print("OpenAI API Response... "f"{output_text}")
        return output_text  

    # ======================================================
    # ---------------- LLM MISTRAL API CALL--------------------
    # ======================================================
    def mistral_call(self,system_prompt,input,api_url,api_key):
        from mistralai import Mistral

        
        model = "mistral-large-latest"

        client = Mistral(api_key=api_key)

        chat_response = client.chat.complete(
            model = model,
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": input,
                },
            ]
        )
        
        output_text = chat_response.choices[0].message.content.strip()
        print("Mistral Response... "f"{output_text}")
        return output_text
    
    
    
    
    # ======================================================
    # ---------------- REVURSIVE OUTPUT VALIDATION-----------
    # ======================================================
    
    def validate_repair_json(self,prompt,policy_grouped,prev_output, cot_reasoning, depth=0):
     # -------- STEP 1: validation prompt (non-JSON) --------
        max_depth=config.MAX_ITERATIONS
        validation_prompt = prompt["validation_prompt"]
        try:
            question = "Policy rule group: \n" + policy_grouped
            """
            if cot_reasoning != '':
                question += "\n Is this reasoning logical: \n" + cot_reasoning
            """
            question += "\n Proposed repair JSON: \n" + json.dumps(prev_output, indent=2)
            
            validation_text = self.llm_call(validation_prompt, question)
            output = self.format_output(validation_text)
            
          #  print(f"validation: Response JSON {depth + 1}:{json.dumps(output, indent=2, ensure_ascii=False)}")


        except Exception as e:
            print(f"validation: JSON formatting failed at {depth + 1} json: {e}")
            return prev_output


        # -------- Convergence check --------
        prev_output = self.ensure_dict_with_keys(prev_output, ["to remove", "to add"])
        output = self.ensure_dict_with_keys(output, ["to remove", "to add"])
        print(f"validation: Response JSON {depth + 1}:{json.dumps(output, indent=2, ensure_ascii=False)}")
        if set(prev_output["to remove"].keys()) == set(output["to remove"].keys()) \
            and set(prev_output["to add"].keys()) == set(output["to add"].keys()):
            print("validation: reasoning converged.")
            return output

        print("validation: reasoning not converged, continuing...")
        
        
        # -------- condition to stop (max reached) --------
        if depth + 1 >= max_depth:
            print("Max recursion depth reached.")
            return prev_output
        else:
            return self.validate_repair_json(
                prompt,
                policy_grouped,
                prev_output=output,
                cot_reasoning='',
                depth=depth + 1,
            )








    def validate_pol_repair(self,prompt,policy_grouped, depth=0):
        # -------- STEP 1: validation prompt (non-JSON) --------
        validation_prompt = prompt["validation_prompt"]
        
        print(f"validation")
        

        try:
            question = "Validate this policy: \n" + policy_grouped
                
            validation_text = self.llm_call(validation_prompt, question)
            output = self.format_output(validation_text)
                
            print(f"validation: Response JSON {depth + 1}:{json.dumps(output, indent=2, ensure_ascii=False)}")
            if "status" in output:
                return True if output["status"] == "VALID" else output["violations"]
        
            else:
                self.validation_count += 1
                return False

        except Exception as e:
            print(f"validation: JSON formatting failed at {depth + 1} json: {e}")
            return False # to remove

    
            
           

     
    # ======================================================
    # ---------------- COT REASONING --------------------
    # ======================================================

    def cot_reasoning(self, prompt, policy_grouped):
        """
        Step-by-step CoT → JSON → repeat until convergence or max_depth
        """

        # -------- STEP 1: reasoning (non-JSON) --------
        reasoning_prompt = prompt["system_prompt"]
        reasoning_text = self.llm_call(reasoning_prompt, policy_grouped)
        #print(f">CoT Reasoning Response:\n{reasoning_text}")
        
        return reasoning_text
    
    
    
    # ======================================================
    # ---------------- Extract JSON from COT --------------------
    # ======================================================
    def format_cot(self, prompt, cot_output,depth):
        """
        Extract JSON from CoT output
        """
       # -------- STEP 2: force JSON --------
        json_prompt = prompt["json_prompt"]
        output = {}
        try:
            output_text = self.llm_call(json_prompt, cot_output)
            output = self.format_output(output_text)
            print(f">{depth + 1}  Response JSON:{json.dumps(output, indent=2, ensure_ascii=False)}")
           
          #  sys.exit()
        except Exception as e:
            print(f">{depth + 1} JSON formatting failed: {e}")
            
        return output
            
    
    


     
     # ======================================================
    # ---------------- MAIN GENERATE METHOD --------------------
    # ======================================================

    def generate(self,prompt, input_policy,property,prev_output,depth=0,prevViolations=None):
        import json
        print(f"generate {depth}")
        temp_policy = copy.deepcopy(input_policy)
        policy_grouped_text=self.policy2text(temp_policy,property)
        
        #if violations found in validation method than add it to next prompt
        policy_grouped_text += "\n Previous violations found in, check only this group: " + json.dumps(prevViolations, indent=2) if prevViolations else ""
        # use CoT reasoning
        if(config.USE_COT):
            cot_output = self.cot_reasoning(prompt,policy_grouped_text)
            cot_json_output = self.format_cot(prompt,cot_output,depth)
            
            # Merge
            existing = prev_output or {}
            new_data = cot_json_output or {}

            # Ensure required keys exist
            existing.setdefault("to remove", {})
            existing.setdefault("to add", {})

            new_remove = new_data.get("to remove", {})
            new_add = new_data.get("to add", {})

            existing["to remove"].update(new_remove)
            existing["to add"].update(new_add)

                        
            if config.USE_VALIDATION:
                max_depth=config.MAX_ITERATIONS
                
                self.repair(temp_policy,cot_json_output,False)  # apply initial repair to get updated policy for validation
                policy_grouped_text=self.policy2text(temp_policy,property)  # regroup after repair to update policy_grouped for validation
                valid = self.validate_pol_repair(prompt,policy_grouped_text)
                print(f"validation result: {valid}")
                if valid == True: 
                    return existing
                else:
                    if depth + 1 >= max_depth:
                        print("Max recursion depth reached.")
                        return existing # return last output even if not valid
                    else:
                        policy_grouped_text=self.policy2text(temp_policy,property)  # regroup after repair to update policy_grouped for validation
                        return self.generate(prompt,temp_policy,property,existing,depth=depth+1,prevViolations=valid)  # re-run the generation with the same prompt and updated policy
            else:
                return existing
            
        
        #use one path reasoning
        else:
            
            try:
                output_text=self.llm_call(prompt["system_prompt"],policy_grouped_text)
                output_text= self.format_output(output_text)
                
                if config.USE_VALIDATION:
                                # Merge
                    existing = prev_output or {}
                    new_data = output_text or {}

                    # Ensure required keys exist
                    existing.setdefault("to remove", {})
                    existing.setdefault("to add", {})

                    new_remove = new_data.get("to remove", {})
                    new_add = new_data.get("to add", {})

                    existing["to remove"].update(new_remove)
                    existing["to add"].update(new_add)
                    
                    max_depth=config.MAX_ITERATIONS
                    
                    self.repair(temp_policy,output_text,False)  # apply initial repair to get updated policy for validation
                    policy_grouped_text=self.policy2text(temp_policy,property)  # regroup after repair to update policy_grouped for validation
                    valid = self.validate_pol_repair(prompt,policy_grouped_text)
                    print(f"validation result: {valid}")
                    if valid == True: 
                        return existing
                    else:
                        if depth + 1 >= max_depth:
                            print("Max recursion depth reached.")
                            return existing # return last output even if not valid
                        else:
                            policy_grouped_text=self.policy2text(temp_policy,property)  # regroup after repair to update policy_grouped for validation
                            return self.generate(prompt,temp_policy,property,existing,depth=depth+1,prevViolations=valid)  # re-run the generation with the same prompt and updated policy
                else:
                    return output_text

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
            # Clean out ```json or ``` wrappers
        


    
    
    def repair(self,policy,repair,final_repair=False):
        
        if not repair or ("to add" not in repair and "to remove" not in repair):
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
       









    def policy2text(self,policy,property):
        policy.group_rules()  # regroup after repair to update policy_grouped for validation
        if(property=="relev"):
            policy_grouped_text = policy.grouped_conditions_text
        elif(property=="la"):
            policy_grouped_text = policy.grouped_rules_text
        elif(property=="consist"):
            policy_grouped_text = policy.grouped_elements_text
 
        return policy_grouped_text
 
    def list_to_text(self,input):
        return "\n".join(input)


    def format_output(self,output):
        output_text = re.sub(r"^```(?:json)?|```$", "", output, flags=re.MULTILINE).strip()
       
        if(output_text==""):
            output_text='{}'
        output={}
        
        return json.loads(output_text)
    
    
    def ensure_dict_with_keys(self,obj, keys):
        if not isinstance(obj, dict):
            return {k: {} for k in keys}

        for k in keys:
            if k not in obj or not isinstance(obj[k], dict):
                obj[k] = {}

        return obj
    
 
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