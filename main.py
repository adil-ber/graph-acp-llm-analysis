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

# Configure simple logging to stdout
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

EVALUATION_FILE = Path(__file__).parent / "evaluation" / "evaluation_results.txt"


import requests


def check_api():


    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": "test"}]
    }

    try:
        response = requests.post(config.API_URL, headers=config.HEADERS, json=data, timeout=10)

        if response.status_code == 200:
            return True   # URL + key are valid
        else:
            print(f"API check failed: {response.status_code} - {response.text}")
            sys.exit(1)  # exit program

    except Exception as e:
        print("API connection error:", e)
        sys.exit(1)  # exit program






def process_model(model: LLM_Model, property_checked) -> None:
    """
    Run checks and evaluation for a single model instance.
    Errors are caught and logged so one failing model won't stop the run.
    """

    logger.info("Model: %s", model.model_name)
    repaired = copy.deepcopy(model.input_policy)

    try:
        if property_checked not in ["relev","consist","la","all"]:
            raise ValueError(f"Unknown property: {property_checked}")
        
        else:
            if property_checked == "relev" or property_checked=="all": # Satisfiability check
                repaired = model.anomaly_checking(repaired,Rel_LLM(model))

            if property_checked == "consist" or property_checked=="all":  #consistency checking
                repaired = model.anomaly_checking(repaired,Consistency_LLM(model))

            if property_checked == "la" or property_checked=="all":# least astonishment checking
                repaired = model.anomaly_checking(repaired,Astonishment_LLM(model))


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
    
    check_api() # Verify API connectivity before proceeding
    
    property_checked=config.PROPERTY  # e.g., "relev", "consist", "la", "all"
    results = {model: {} for model in config.MODELS} #init results
    
    # Iterate configured models
    for  model_name in config.MODELS:
 
        # Write a run header once
        with EVALUATION_FILE.open("a", encoding="utf-8") as f:
            f.write(f"\n-------- {model_name} ---------\n")
            
        # Iterate configured policies
        for policy_id in config.POLICIES:
            
            # Create input and expected policy objects
            input_policy = Policy(policy_id, "input")
            expected_policy = Policy(policy_id, "expected",property_checked)
            
            llm = LLM_Model(model_name, input_policy)
            repaired_policy=process_model(llm, property_checked)
            print(f"------ {policy_id} ------")
            # Evaluate repaired policy against expected policy and log to file
            results[model_name][policy_id] = Evaluator.evaluate(model_name, policy_id, repaired_policy, expected_policy)
            
            # Optionally export repaired policy:
            #repaired.policy_export()
            
            # Visual separation in console output
            logger.info("---------------")
        
        # log to file the average results per model
        averages = Evaluator.model_results_average(property_checked,results[model_name]) 



if __name__ == "__main__":
    main()
