from governance_rules import evaluate_governance


tests = [
    {
        "rule_type": "approval",
        "active": True,
        "magnitude": 50000
    },
    {
        "rule_type": "normal",
        "active": True,
        "magnitude": 50000
    },
    {
        "rule_type": "normal",
        "active": True,
        "magnitude": 150000
    },
    {
        "rule_type": "normal",
        "active": False,
        "magnitude": 50000
    }
]


for test in tests:
    result = evaluate_governance(test)

    print("\nInput:")
    print(test)

    print("Output:")
    print(result)