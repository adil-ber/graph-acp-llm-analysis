"""
Entry point for running policy checks and evaluation across configured LLM models.

This refactor:
- wraps execution in a main() function
- adds comments and basic logging
- isolates per-model processing with error handling
- writes a single evaluation header and appends per-model results
"""
from pathlib import Path
import logging
import copy
from policy_preprocessing.Policy import Policy
from evaluation.evaluation import Evaluator
from analyzers.llm_analyzer import LLM_Model
from analyzers.relevancy_analyzer import Rel_LLM
from analyzers.consistency_analyzer import Consistency_LLM
from analyzers.astonishment_analyzer import Astonishment_LLM
import config,sys
import argparse

# Configure simple logging to stdout
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

EVALUATION_FILE = Path(__file__).parent / "evaluation" / "evaluation_results.txt"


import requests




def main() -> None:
    """
    Main orchestration: prepare policies, create evaluation header and iterate models.
    """
    
    for model in config.MODELS:
        input_policy = Policy("policy44","input")
        
        
        
        llmModel = LLM_Model(model,input_policy)

        llm_input = [f"{key}: {value}" for key, value in input_policy.rules.items()]
        input = llmModel.list_to_text(llm_input)
        
        input = input_policy.grouped_rules_text
        print(f"LLM INPUT: {input} \n\n")
        
        
        system_prompt=llmModel.getFileContent("prompts","prompt4_cot_astonishment.txt")
            
        payload = {
                "model": llmModel.model_name,
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
            
        print(f"Generated output: {output_text}")
        
        
        """ 
            system_prompt=llmModel.getFileContent("prompts","prompt4_repair_astonishment.txt")
                
            payload = {
                    "model": llmModel.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": output_text}
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
                
            print(f"Final output: {output_text}")
         """

if __name__ == "__main__":
    main()
