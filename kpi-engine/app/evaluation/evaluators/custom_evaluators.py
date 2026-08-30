from typing import Any
from langsmith.evaluation import EvaluationResult, run_evaluator
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

@run_evaluator
def evaluate_evidence_grounding(run: Any, example: Any) -> EvaluationResult:
    """
    LLM-as-a-judge evaluator to verify that the final story/output 
    is fully grounded in the retrieved evidence (no hallucinations).
    """
    predicted_output = run.outputs
    reference_output = example.outputs if example else None
    
    # Simple check for illustration; in reality we'd prompt an LLM judge
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    prompt = PromptTemplate.from_template(
        "Evaluate the following output for evidence grounding against the expected output.\n"
        "Score 1 if fully grounded, 0 otherwise.\n\n"
        "Output: {output}\nExpected: {expected}\n\nScore:"
    )
    
    score_str = llm.invoke(prompt.format(output=str(predicted_output), expected=str(reference_output))).content.strip()
    score = 1.0 if score_str == "1" else 0.0
    
    return EvaluationResult(
        key="evidence_grounding",
        score=score,
        comment="Grounded" if score == 1.0 else "Not grounded"
    )

@run_evaluator
def evaluate_contradiction_handling(run: Any, example: Any) -> EvaluationResult:
    """
    Deterministic evaluator to check if a known contradiction case was properly
    flagged in the diagnostic payload.
    """
    # Assuming the run outputs contain the diagnostic payload
    payload = run.outputs.get("diagnostic_payload", {})
    has_contradiction_flag = payload.get("has_contradiction", False)
    
    expected_flag = example.outputs.get("diagnostic_payload", {}).get("has_contradiction", False)
    
    score = 1.0 if has_contradiction_flag == expected_flag else 0.0
    
    return EvaluationResult(
        key="contradiction_handling",
        score=score,
        comment="Matched expected contradiction flag."
    )
