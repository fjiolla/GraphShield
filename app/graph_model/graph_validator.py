"""
Graph validator module.
"""

import networkx as nx
import logging

logger = logging.getLogger(__name__)

def check_graph_not_empty(G: nx.Graph) -> tuple:
    """Check graph has nodes and edges. Return (passed: bool, message: str)"""
    if G.number_of_nodes() == 0:
        return False, "Graph has zero nodes."
    if G.number_of_edges() == 0:
        return False, "Graph has zero edges. Structural metrics cannot be computed."
    return True, "Graph is not empty."

def check_nodes_have_attributes(G: nx.Graph) -> tuple:
    """Check nodes have at least some attributes beyond just ID."""
    has_attrs = False
    for _, data in G.nodes(data=True):
        if len(data) > 0:
            has_attrs = True
            break
    if not has_attrs:
        return False, "Nodes have no attributes."
    return True, "Nodes have attributes."

def check_protected_attr_exists(G: nx.Graph, attr: str) -> tuple:
    """Check if given attribute name exists on nodes."""
    if not attr:
        return False, "No protected attribute specified."
    found = False
    for _, data in G.nodes(data=True):
        if attr in data:
            found = True
            break
    if not found:
        return False, f"Protected attribute '{attr}' not found on nodes."
    return True, f"Protected attribute '{attr}' found."

def check_predictions_on_nodes(G: nx.Graph) -> tuple:
    """
    Check if any node attribute looks like a prediction/score/outcome.
    Look for columns containing: 'pred', 'score', 'label', 
    'outcome', 'result', 'flag', 'risk'
    Return (found: bool, candidate_columns: list)
    """
    candidates = ['pred', 'score', 'label', 'outcome', 'result', 'flag', 'risk']
    found_cols = set()
    for _, data in G.nodes(data=True):
        for k in data.keys():
            k_lower = str(k).lower()
            if any(c in k_lower for c in candidates):
                found_cols.add(k)
    return len(found_cols) > 0, list(found_cols)

def check_graph_connectivity(G: nx.Graph) -> tuple:
    """Check if graph is connected. Warn if fragmented."""
    if G.number_of_nodes() == 0:
        return False, "Empty graph."
    undir_G = G.to_undirected() if G.is_directed() else G
    is_conn = nx.is_connected(undir_G)
    msg = "Graph is connected." if is_conn else "Graph is fragmented into multiple components."
    return is_conn, msg

def validate_graph(graph_data: dict, protected_attr: str = None) -> dict:
    """
    Run all validation checks on loaded graph.
    """
    G = graph_data["graph"]
    errors = []
    warnings = []
    suggestions = []
    
    # Not empty
    passed, msg = check_graph_not_empty(G)
    if not passed:
        errors.append(msg)
    
    if G.number_of_nodes() > 0 and G.number_of_nodes() < 10:
        warnings.append("Graph is very small (< 10 nodes). Fairness metrics may be unreliable.")
        
    # Attrs
    passed, msg = check_nodes_have_attributes(G)
    if not passed:
        errors.append(msg)
        
    # Protected attr
    protected_attr_found = False
    if protected_attr:
        passed, msg = check_protected_attr_exists(G, protected_attr)
        if not passed:
            errors.append(msg)
        else:
            protected_attr_found = True
            
    # Predictions
    has_preds, pred_cols = check_predictions_on_nodes(G)
    if has_preds:
        suggestions.append(f"Auto-detected potential prediction columns: {pred_cols}")
        
    # Connectivity
    is_conn, msg = check_graph_connectivity(G)
    if not is_conn:
        warnings.append(msg)
        
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "has_predictions": has_preds,
        "has_ground_truth": False, # Basic assumption
        "protected_attr_found": protected_attr_found
    }

if __name__ == "__main__":
    G = nx.path_graph(5)
    nx.set_node_attributes(G, 1, "age")
    G.nodes[0]['pred'] = 0.9
    val = validate_graph({"graph": G}, "age")
    print("Validation:", val)
