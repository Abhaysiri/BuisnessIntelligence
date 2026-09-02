from typing import Any
from langsmith.evaluation import EvaluationResult, run_evaluator
from langchain.prompts import PromptTemplate
from app.llm_client import get_chat_llm

from pydantic import BaseModel, Field

class JudgeResponse(BaseModel):
    rationale: str = Field(description="Step-by-step extraction of claims and verification against the evidence.")
    score: int = Field(description="1 if all claims are fully grounded in the evidence, 0 if there is any hallucinated or unsupported claim.")

@run_evaluator
def evaluate_evidence_grounding(run: Any, example: Any) -> EvaluationResult:
    """
    LLM-as-a-judge evaluator to verify that the final story/output 
    is fully grounded in the retrieved evidence (no hallucinations).
    """
    predicted_output = run.outputs.get("story", "") if run.outputs else ""
    
    # We should evaluate against the actual retrieved evidence, not the golden expected output.
    # In a real LangSmith trace, the inputs or intermediate steps contain the diagnostic payload.
    # We'll extract it from the run's inputs or outputs.
    diagnostic_payload = run.inputs.get("diagnostic_payload", "") if run.inputs else ""
    if not diagnostic_payload and run.outputs:
        diagnostic_payload = run.outputs.get("diagnostic_payload", "")
    
    llm = get_chat_llm(temperature=0).with_structured_output(JudgeResponse)
    
    prompt = PromptTemplate.from_template(
        "You are an expert evaluator. Your task is to verify if the generated story is fully grounded in the provided diagnostic evidence.\n\n"
        "DIAGNOSTIC EVIDENCE:\n{evidence}\n\n"
        "GENERATED STORY:\n{story}\n\n"
        "Instructions:\n"
        "1. Extract all factual claims, numbers, and dimensions from the story.\n"
        "2. Cross-reference each claim against the DIAGNOSTIC EVIDENCE.\n"
        "3. If ANY claim in the story cannot be proven by the evidence, score it as 0.\n"
        "4. If ALL claims are supported by the evidence, score it as 1.\n"
        "5. Provide your step-by-step rationale before scoring."
    )
    
    try:
        response: JudgeResponse = llm.invoke(
            prompt.format(story=str(predicted_output), evidence=str(diagnostic_payload))
        )
        
        return EvaluationResult(
            key="evidence_grounding",
            score=float(response.score),
            comment=response.rationale
        )
    except Exception as e:
        return EvaluationResult(
            key="evidence_grounding",
            score=0.0,
            comment=f"Evaluator failed to parse output: {str(e)}"
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
