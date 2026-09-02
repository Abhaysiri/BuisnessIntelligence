import os
import argparse
from langsmith import evaluate
from app.monitoring.tracing import get_langsmith_client
from app.evaluation.evaluators.custom_evaluators import evaluate_evidence_grounding, evaluate_contradiction_handling

# Mock target function representing the KPI engine pipeline
def run_kpi_pipeline(inputs: dict):
    """
    This function wraps the main LangGraph/orchestrator entry point.
    In a real implementation, you would import and call the orchestrator graph here.
    """
    # from app.orchestrator.graph import graph
    # return graph.invoke(inputs)
    return {"diagnostic_payload": {"has_contradiction": False}, "story": "Example story"}

def main():
    parser = argparse.ArgumentParser(description="Run LangSmith offline evaluations")
    parser.add_argument("--dataset", type=str, default="kpi-golden-dataset", help="Name of the dataset to evaluate")
    parser.add_argument("--experiment-prefix", type=str, default="kpi-engine-eval", help="Prefix for the experiment name")
    args = parser.parse_args()

    client = get_langsmith_client()
    if not client:
        print("LangSmith client not initialized. Ensure environment variables are set.")
        return

    evaluators = [
        evaluate_evidence_grounding,
        evaluate_contradiction_handling
    ]

    print(f"Starting evaluation on dataset: {args.dataset}")
    
    import sys
    
    try:
        experiment_results = evaluate(
            run_kpi_pipeline,
            data=args.dataset,
            evaluators=evaluators,
            experiment_prefix=args.experiment_prefix,
            client=client
        )
        print("Evaluation complete. View results in LangSmith.")
        
        # Calculate pass rate
        total_scores = 0
        total_evals = 0
        
        for result in experiment_results:
            eval_results = result.get("evaluation_results", {})
            results_list = eval_results.get("results", [])
            for eval_res in results_list:
                score = getattr(eval_res, 'score', None)
                if score is not None:
                    total_scores += score
                    total_evals += 1
                    
        if total_evals > 0:
            average_score = total_scores / total_evals
            print(f"Aggregate Evaluation Score: {average_score:.2%}")
            
            # Fail the CI pipeline if average score drops below 90%
            if average_score < 0.90:
                print("Error: Average evaluation score is below the 90% threshold. Failing CI check.")
                sys.exit(1)
        else:
            print("No evaluation scores recorded.")
            
    except Exception as e:
        print(f"Evaluation failed. Make sure the dataset exists: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
