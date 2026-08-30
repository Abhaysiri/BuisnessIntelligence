import logging
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.monitoring.tracing import langsmith_client
from app.config import settings

logger = logging.getLogger(__name__)

class FeedbackRequest(BaseModel):
    trace_id: str
    reviewer_role: str
    verdict: int # e.g. 0 or 1, or 1 to 5
    error_category: Optional[str] = None
    correction: Optional[Dict[str, Any]] = None
    comments: Optional[str] = None

def submit_feedback(feedback: FeedbackRequest):
    """
    Submits user feedback to LangSmith for a given trace.
    It attaches the feedback to the original trace ID and then
    adds it to a dataset for future evaluation.
    """
    if not langsmith_client:
        logger.warning("LangSmith client not initialized. Feedback not recorded.")
        return False
        
    try:
        # Try to read the run to get the session_id to avoid the deprecation warning
        try:
            run = langsmith_client.read_run(run_id=feedback.trace_id)
            session_id = run.session_id if hasattr(run, 'session_id') else None
        except Exception:
            session_id = None
            
        # Create feedback on the run
        feedback_kwargs = {
            "run_id": feedback.trace_id,
            "key": "human_review",
            "score": feedback.verdict,
            "value": feedback.error_category,
            "comment": feedback.comments,
            "source_info": {"reviewer_role": feedback.reviewer_role}
        }
        if session_id:
            feedback_kwargs["session_id"] = session_id

        feedback_result = langsmith_client.create_feedback(**feedback_kwargs)
        
        # If there's a correction and it's a negative verdict, add it to our CI/CD dataset
        if feedback.correction and feedback.verdict < 1: # Assuming 1 is max score or 0 is bad
            add_to_evaluation_dataset(feedback.trace_id, feedback.correction)
            
        return True
    except Exception as e:
        if "403" in str(e) or "Forbidden" in str(e):
            logger.error("403 Forbidden Error: Your LangSmith API key is invalid or lacks the necessary permissions. Please check your .env file.")
        else:
            logger.error(f"Error submitting feedback to LangSmith: {e}")
        return False

def add_to_evaluation_dataset(trace_id: str, correction: Dict[str, Any], dataset_name: str = "kpi-corrections-dataset"):
    """
    Retrieves the run and adds it to an evaluation dataset along with the provided correction.
    """
    try:
        if not langsmith_client:
            return

        run = langsmith_client.read_run(run_id=trace_id)
        
        # Ensure the dataset exists
        if not langsmith_client.has_dataset(dataset_name=dataset_name):
            langsmith_client.create_dataset(dataset_name=dataset_name, description="Human corrected traces")
            
        # Add example to dataset
        langsmith_client.create_example(
            inputs=run.inputs,
            outputs=correction,
            dataset_name=dataset_name
        )
        logger.info(f"Added trace {trace_id} to dataset {dataset_name} as an example.")
        
    except Exception as e:
        logger.error(f"Failed to add trace {trace_id} to dataset: {e}")
