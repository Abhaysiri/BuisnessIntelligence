import logging
from langsmith import Client
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DatasetManager:
    def __init__(self, client: Client):
        self.client = client

    def create_or_get_dataset(self, name: str, description: str = ""):
        """Create a new dataset or return the existing one."""
        if self.client.has_dataset(dataset_name=name):
            return self.client.read_dataset(dataset_name=name)
        return self.client.create_dataset(dataset_name=name, description=description)

    def populate_golden_dataset(self, dataset_name: str, examples: List[Dict[str, Any]]):
        """
        Populate the dataset with golden examples.
        Each example should have 'inputs' and 'outputs'.
        """
        dataset = self.create_or_get_dataset(dataset_name)
        
        for ex in examples:
            inputs = ex.get("inputs", {})
            outputs = ex.get("outputs", {})
            metadata = ex.get("metadata", {})
            
            self.client.create_example(
                inputs=inputs,
                outputs=outputs,
                metadata=metadata,
                dataset_id=dataset.id
            )
        logger.info(f"Populated dataset {dataset_name} with {len(examples)} examples.")
