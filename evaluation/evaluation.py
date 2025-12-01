from pathlib import Path

class Evaluator:

    # ======================================================
    # ---- Shared function: TP, FP, FN, values comparison ---
    # ======================================================
    @staticmethod
    def compute_confusion_values(expected_policy, repaired_policy):
        p1 = expected_policy.rules
        p2 = repaired_policy.rules

        expected_values = set(p1.values())
        repaired_values = set(p2.values())

        tp = len(expected_values & repaired_values)
        fn = len(expected_values - repaired_values)
        fp = len(repaired_values - expected_values)

        # TN is undefined in this scenario
        tn = 0

        return {
            "expected_values": expected_values,
            "repaired_values": repaired_values,
            "missing_values": list(expected_values - repaired_values),
            "extra_values": list(repaired_values - expected_values),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "total_expected": len(expected_values),
            "total_repaired": len(repaired_values),
        }

    # ======================================================
    # ---------------- Metric Functions --------------------
    # ======================================================
    @staticmethod
    def precision(tp, fp):
        denom = tp + fp
        if denom == 0:
            return 0.0
        return (tp / denom) * 100

    @staticmethod
    def recall(tp, fn):
        denom = tp + fn
        if denom == 0:
            return 0.0
        return (tp / denom) * 100

    @staticmethod
    def f1(precision, recall):
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)

    @staticmethod
    def accuracy(tp, fp, fn):
        # total = tp + fp + fn
        denom = tp + fp + fn
        if denom == 0:
            return 0.0
        return (tp / denom) * 100

    # ======================================================
    # ----------------- Evaluate Function ------------------
    # ======================================================
    def evaluate(model, policy_id, repaired_policy, expected_policy):

        # ---- Use shared confusion computation ----
        data = Evaluator.compute_confusion_values(expected_policy, repaired_policy)

        tp = data["tp"]
        fp = data["fp"]
        fn = data["fn"]
        # tn = data["tn"]  # still unused

        # ---- Compute metrics using shared values ----
        precision = Evaluator.precision(tp, fp)
        recall = Evaluator.recall(tp, fn)
        f1 = Evaluator.f1(precision, recall)
        accuracy = Evaluator.accuracy(tp, fp, fn)

        # ---- Pack final results ----
        errors = {
            "model": model,
            "property_checked": policy_id,
            "missing_values": data["missing_values"],
            "extra_values": data["extra_values"],
            "count_correct": tp,
            "count_expected": data["total_expected"],
            "count_repaired": data["total_repaired"],
            "score_precision": round(precision, 2),
            "score_recall": round(recall, 2),
            "score_f1": round(f1, 2),
            "score_accuracy": round(accuracy, 2),
        }

        # Show result
        import pprint
        pprint.pprint(errors, indent=4)

        Evaluator.writeEvaluation(errors)

        return errors
    
    
    def model_results_average(property_checked,model_results):
        # model_results = results[model_name]
        precision_sum = 0
        recall_sum = 0
        f1_sum = 0
        accuracy_sum = 0
        n = len(model_results)
 
        for policy_id, metrics in model_results.items():
            precision_sum += metrics["score_precision"]
            recall_sum += metrics["score_recall"]
            f1_sum += metrics["score_f1"]
            accuracy_sum += metrics["score_accuracy"]

        scores= {
            "property_checked": property_checked,
            "score_precision": precision_sum / n if n else 0,
            "score_recall": recall_sum / n if n else 0,
            "score_f1": f1_sum / n if n else 0,
            "score_accuracy": accuracy_sum / n if n else 0
        }
        
        import pprint
        pprint.pprint(scores, indent=4)

        Evaluator.writeEvaluation(scores)
        
        return scores


    # ======================================================
    # ----------------- Write to File ----------------------
    # ======================================================
    def writeEvaluation(results):
        EVALUATION_FILE = Path(__file__).parent / "evaluation_results.txt"
        with EVALUATION_FILE.open("a", encoding="utf-8") as f:
            values = [
                "   " + str(results['property_checked']),
                "  prec: " + str(results['score_precision']),
                "  rec: " + str(results['score_recall']),
                "  f1: " + str(results['score_f1']),
                "  acc: " + str(results['score_accuracy'])
            ]
            f.write(','.join(values) + "\n")

