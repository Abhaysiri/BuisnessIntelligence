import networkx as nx
from app.schemas.findings import AgentFinding


def build_kpi_dependency_graph() -> nx.DiGraph:
    G = nx.DiGraph()

    # Define nodes with categories
    nodes = {
        "revenue": {"type": "kpi"},
        "orders": {"type": "kpi"},
        "conversion_rate": {"type": "kpi"},
        "average_order_value": {"type": "kpi"},
        "qualified_sessions": {"type": "kpi"},
        "traffic": {"type": "driver"},
        "marketing_spend": {"type": "driver"},
        "checkout_error_rate": {"type": "driver"},
        "price": {"type": "driver"},
        "product_mix": {"type": "driver"},
        "inventory_availability": {"type": "driver"},
        "fx_rate": {"type": "external_factor"},
        "product": {"type": "dimension"},
        "customer_segment": {"type": "dimension"},
        "geography": {"type": "dimension"},
        "sales_channel": {"type": "dimension"},
        "device_os": {"type": "dimension"}
    }
    for node, attrs in nodes.items():
        G.add_node(node, **attrs)

    # Define edges & relationship semantics
    edges = [
        ("marketing_spend", "traffic", "influences"),
        ("traffic", "qualified_sessions", "influences"),
        ("checkout_error_rate", "conversion_rate", "influences"),
        ("qualified_sessions", "conversion_rate", "influences"),
        ("conversion_rate", "orders", "influences"),
        ("orders", "revenue", "mathematical"),
        ("average_order_value", "revenue", "mathematical"),
        ("fx_rate", "revenue", "transforms"),
        ("product", "revenue", "decomposes"),
        ("customer_segment", "revenue", "decomposes"),
        ("geography", "revenue", "decomposes"),
        ("sales_channel", "revenue", "decomposes"),
        ("device_os", "conversion_rate", "influences")
    ]
    for src, dst, rel in edges:
        G.add_edge(src, dst, relation=rel)

    return G


# Global static graph
DEPENDENCY_GRAPH = build_kpi_dependency_graph()


def validate_dependency(finding: AgentFinding, target_kpi: str = "revenue") -> dict:
    """
    Validates whether the claimed driver or dimension has a valid causal / mathematical
    path to the affected KPI in the dependency graph.
    """
    driver_type = finding.driver_type.lower() if finding.driver_type else ""
    target = target_kpi.lower()

    # Check direct dimension linkage
    dimension_keys = list(finding.dimension.keys())
    
    valid_paths = []
    has_valid_path = False

    # Check driver type against graph
    if driver_type in DEPENDENCY_GRAPH and target in DEPENDENCY_GRAPH:
        if nx.has_path(DEPENDENCY_GRAPH, driver_type, target):
            valid_paths.append(list(nx.all_simple_paths(DEPENDENCY_GRAPH, driver_type, target)))
            has_valid_path = True

    # Check dimensions against graph
    for dim in dimension_keys:
        dim_key = dim.lower()
        if dim_key in DEPENDENCY_GRAPH and target in DEPENDENCY_GRAPH:
            if nx.has_path(DEPENDENCY_GRAPH, dim_key, target):
                valid_paths.append(list(nx.all_simple_paths(DEPENDENCY_GRAPH, dim_key, target)))
                has_valid_path = True

    # If neither driver_type nor dimension are strict nodes, default to validating if evidence metrics connect
    for ev in finding.evidence:
        if ev.metric and ev.metric.lower() in DEPENDENCY_GRAPH and target in DEPENDENCY_GRAPH:
            if nx.has_path(DEPENDENCY_GRAPH, ev.metric.lower(), target):
                has_valid_path = True

    return {
        "status": "SUPPORTED" if has_valid_path else "UNSUPPORTED_OR_UNKNOWN",
        "is_valid": has_valid_path or len(dimension_keys) > 0
    }
