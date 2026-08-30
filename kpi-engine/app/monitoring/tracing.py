import os
import logging
from langsmith import Client
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.tracers.context import tracing_v2_enabled
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize LangSmith client
def get_langsmith_client() -> Client | None:
    if not settings.langsmith_tracing:
        return None
        
    try:
        # Set environment variables for langchain core to pick them up
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key or ""
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
        
        return Client(api_key=settings.langsmith_api_key)
    except Exception as e:
        logger.warning(f"Failed to initialize LangSmith client: {e}")
        return None

langsmith_client = get_langsmith_client()

def get_tracing_context(project_name=None):
    """
    Context manager to enforce tracing with a specific project name.
    If tracing is disabled, returns a dummy context manager.
    """
    if not settings.langsmith_tracing:
        import contextlib
        @contextlib.contextmanager
        def dummy_context():
            yield
        return dummy_context()
        
    return tracing_v2_enabled(project_name=project_name or settings.langsmith_project)

class CustomObservabilityCallback(BaseCallbackHandler):
    """
    Custom callback to extract specific metrics and log them separately if needed.
    (LangSmith's built-in tracer will handle the bulk of the work automatically).
    """
    
    def on_chain_start(self, serialized, inputs, **kwargs):
        pass
        
    def on_chain_end(self, outputs, **kwargs):
        pass
        
    def on_llm_start(self, serialized, prompts, **kwargs):
        pass
        
    def on_llm_end(self, response, **kwargs):
        pass
