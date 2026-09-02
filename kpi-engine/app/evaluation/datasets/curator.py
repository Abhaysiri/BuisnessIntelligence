import os
import sys
from app.monitoring.tracing import get_langsmith_client

def main():
    client = get_langsmith_client()
    if not client:
        print("LangSmith client not initialized. Ensure environment variables are set.")
        sys.exit(1)

    raw_dataset_name = "kpi-corrections-dataset"
    golden_dataset_name = "kpi-golden-dataset"

    # Ensure datasets exist
    try:
        raw_dataset = client.read_dataset(dataset_name=raw_dataset_name)
    except Exception:
        print(f"No raw dataset found named '{raw_dataset_name}'. No corrections to review.")
        sys.exit(0)

    try:
        golden_dataset = client.read_dataset(dataset_name=golden_dataset_name)
    except Exception:
        print(f"Creating golden dataset '{golden_dataset_name}'.")
        golden_dataset = client.create_dataset(dataset_name=golden_dataset_name, description="Golden evaluation cases")

    examples = list(client.list_examples(dataset_id=raw_dataset.id))
    
    if not examples:
        print("No raw corrections to review.")
        sys.exit(0)

    print(f"Found {len(examples)} corrections to review.\n")
    
    for example in examples:
        print("="*60)
        print(f"Example ID: {example.id}")
        if hasattr(example, 'metadata') and example.metadata and 'user_comment' in example.metadata:
            print(f"--- USER COMMENT ---\n{example.metadata['user_comment']}")
        print("--- INPUTS ---")
        print(example.inputs)
        print("--- PROPOSED OUTPUT (CORRECTION) ---")
        print(example.outputs)
        print("="*60)
        
        choice = input("Accept (a), Reject (r), Skip (s)? [a/r/s]: ").strip().lower()
        
        if choice == 'a':
            # Add to golden dataset (preserving metadata)
            client.create_example(
                inputs=example.inputs,
                outputs=example.outputs,
                metadata=example.metadata if hasattr(example, 'metadata') else None,
                dataset_id=golden_dataset.id
            )
            print("=> Added to golden dataset.")
            # Remove from raw dataset
            client.delete_example(example_id=example.id)
            print("=> Removed from raw corrections dataset.")
        elif choice == 'r':
            client.delete_example(example_id=example.id)
            print("=> Rejected and removed from raw corrections dataset.")
        else:
            print("=> Skipped.")
            
    print("\nCuration session complete.")

if __name__ == "__main__":
    main()
