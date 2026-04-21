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


def get_arguments_value():
    """
    Load the input policy based on the given policy file.
    """
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Access Control Policy Analyzer")
    
    parser.add_argument("--task", "-t",
                        type=str,
                        required=False,
                        help="Path to input policy file")
    
    parser.add_argument("--model", "-m",
                        type=str,
                        required=False,
                        help="Path to input policy file")
      
    parser.add_argument("--input", "-i",
                        type=str,
                        required=False,
                        help="Path to input policy file")
    
    parser.add_argument("--expected", "-e",
                        type=str,
                        required=False,
                        help="Path to input policy file")


    args = parser.parse_args()
    arg_value = {}
    
    arg_value["task"] = args.task
    arg_value["model"] = args.input
    arg_value["input"] = args.input
    arg_value["expected"] = args.input
    
    return arg_value




    # ======================================================
    # ---------------- ANOMALY CHECK PER ANOMALY TYPE-------
    # ======================================================
def anomaly_checking(policy,anomaly_type):   
        #try:
            repaired_policy = copy.deepcopy(policy)
            anomaly_type.check(repaired_policy)
            
       # except Exception as exc:   
        #    print(f"Error during anomaly checking: {exc}")
            return repaired_policy



def process_model(model: LLM_Model, property_checked, input_policy) -> None:
    """
    Run checks and evaluation for a single model instance.
    Errors are caught and logged so one failing model won't stop the run.
    """
    print(f"{model.validation_count} validations so far for {model.model_name}")
    logger.info("Model: %s", model.model_name)
    repaired = copy.deepcopy(input_policy)
    try:
        if property_checked not in ["relev","consist","la","all"]:
            raise ValueError(f"Unknown property: {property_checked}")
        
        else:
            if property_checked == "relev" or property_checked=="all": # Satisfiability check
                repaired = anomaly_checking(repaired,Rel_LLM(model))
                
            if property_checked == "la" or property_checked=="all":# least astonishment checking
                repaired = anomaly_checking(repaired,Astonishment_LLM(model))

            if property_checked == "consist" or property_checked=="all":  #consistency checking
                repaired = anomaly_checking(repaired,Consistency_LLM(model))




        return repaired
    

    except Exception as exc:
        # Record the exception to the evaluation file for later inspection
        logger.exception("Error while processing model %s: %s", model.model_name, exc)
        with EVALUATION_FILE.open("a", encoding="utf-8") as f:
            f.write(f"\nModel: {model.model_name} - ERROR: {exc}\n")



def main() -> None:
    """
    Main orchestration: prepare policies, create evaluation header and iterate models.
    """
    

    
    
    #If API is valid, proceed with the evaluation
    property_checked=config.PROPERTY_CHECKED  # e.g., "relev", "consist", "la", "all"
    results = {model: {} for model in config.MODELS} #init results
    validation_count = 0
    # Iterate configured models
    for  model_name in config.MODELS:
        """  if config.USE_MISTRAL:
            model_name = "mistral-medium-latest"  # Override model name for Mistral if enabled
            results[model_name] = {}  # Ensure results dict has entry for Mistral
         """   
        llm = LLM_Model(model_name)
       # llm.llm_api_check() # Verify API connectivity before proceeding
     
        # Write a run header once
        with EVALUATION_FILE.open("a", encoding="utf-8") as f:
            f.write(f"\n-------- {model_name} ---------\n")
            f.write(
                "-------- "
                f"{'INVERSE' if config.USE_INVERTED_RULES else 'ORDERED'} "
                f"{'FEW' if config.USE_FEW_SHOTS else 'ZERO'} "
                f"{'COT' if config.USE_COT else 'DIRECT'} "
                f"{'Validation' if config.USE_VALIDATION else 'NoValidation'} "
                f"{config.POLICY_SIZE} "
                "--------\n"
            )

            
        # Iterate configured policies
        for policy_id in config.POLICIES:
            
            # Create input and expected policy objects
            input_policy = Policy(policy_id, "input", config.POLICY_SIZE)
            expected_policy = Policy(policy_id, "expected", config.POLICY_SIZE, property_checked)
            
            #print(f"{input_policy.grouped_elements_text}")
            
            #print(input_policy.grouped_conditions_text)
            #sys.exit()
            
            repaired_policy=process_model(llm, property_checked,input_policy)
            validation_count=llm.validation_count
            
            print(f"Validation count for {model_name} is {validation_count}")
            print(f"------ {policy_id} ------")
            # Evaluate repaired policy against expected policy and log to file
            results[model_name][policy_id] = Evaluator.evaluate(model_name, policy_id, repaired_policy, expected_policy,validation_count)
            
            # Optionally export repaired policy:
            #repaired.policy_export()
            
            # Visual separation in console output
            logger.info("---------------")
        
        averages = Evaluator.model_results_average(property_checked,results[model_name],llm.validation_count) 
    
    # get arguments values
    """
        args_value= get_arguments_value()
        
        property_checked=args_value["task"]  # get task from arguments (e.g., "relev", "consist", "la", "all")
        model=args_value["model"]  # get llm model from arguments (e.g., "openai/gpt-oss-120b")
        p1=args_value["input"]   # get input policy file from arguments
        p2=args_value["expected"]  # get expected policy file from arguments
    """
    
    


if __name__ == "__main__":
    main()
