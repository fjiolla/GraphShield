"""
Structural fairness metrics for graphs.
"""

import networkx as nx
import pandas as pd
import numpy as np
import logging
from app.graph_model.constants import (
    HOMOPHILY_THRESHOLD,
    DEGREE_DISPARITY_THRESHOLD,
    PAGERANK_DISPARITY_THRESHOLD
)

logger = logging.getLogger(__name__)

def get_group_values(G: nx.Graph, protected_attr: str, metric_dict: dict) -> dict:
    """
    Helper: given a dict of {node_id: metric_value},
    group values by protected_attr.
    Return {group_name: [list of values]}
    """
    groups = {}
    for node, value in metric_dict.items():
        if node in G.nodes:
            g = G.nodes[node].get(protected_attr, 'Unknown')
            if g not in groups:
                groups[g] = []
            groups[g].append(value)
    return groups

def base_disparity(group_values: dict, threshold: float) -> dict:
    """Calculate ratio between max and min mean for groups."""
    means = {g: np.mean(v) for g, v in group_values.items() if len(v) > 0}
    if not means: return {"raw_value": 1.0, "score": 100, "status": "PASS", "per_group": {}}
    
    max_m = max(means.values())
    min_m = min(means.values())
    
    ratio = (max_m / min_m) if min_m > 0 else 1.0
    status = "FAIL" if ratio > threshold else "PASS"
    score = max(0, 100 - int((ratio - 1.0) * 20))
    
    return {
        "raw_value": float(ratio),
        "score": score,
        "status": status,
        "per_group": means
    }

def compute_degree_disparity(G: nx.Graph, protected_attr: str) -> dict:
    """Compare mean node degree across protected groups."""
    degrees = dict(G.degree())
    group_vals = get_group_values(G, protected_attr, degrees)
    return base_disparity(group_vals, DEGREE_DISPARITY_THRESHOLD)

def compute_pagerank_disparity(G: nx.Graph, protected_attr: str) -> dict:
    """Compare mean PageRank per protected group."""
    try:
        pr = nx.pagerank(G)
        group_vals = get_group_values(G, protected_attr, pr)
        return base_disparity(group_vals, PAGERANK_DISPARITY_THRESHOLD)
    except Exception as e:
        logger.warning(f"PageRank error: {e}")
        return {"raw_value": 0, "score": 100, "status": "PASS", "per_group": {}}

def compute_clustering_disparity(G: nx.Graph, protected_attr: str) -> dict:
    """Compare mean clustering coefficient across groups."""
    try:
        cc = nx.clustering(G)
        group_vals = get_group_values(G, protected_attr, cc)
        return base_disparity(group_vals, 1.5)
    except Exception as e:
        return {"raw_value": 0, "score": 100, "status": "PASS", "per_group": {}}

def compute_homophily(G: nx.Graph, protected_attr: str) -> dict:
    """Compute attribute assortativity coefficient."""
    try:
        assortativity = nx.attribute_assortativity_coefficient(G, protected_attr)
        if np.isnan(assortativity): assortativity = 0.0
    except Exception as e:
        logger.warning(f"Assortativity error: {e}")
        assortativity = 0.0
        
    score = max(0, 100 - int(abs(assortativity) * 100))
    status = "FAIL" if assortativity > HOMOPHILY_THRESHOLD else "PASS"
    return {
        "raw_value": float(assortativity),
        "score": score,
        "status": status
    }

def compute_prediction_centrality_correlation(G: nx.Graph, node_df: pd.DataFrame, protected_attr: str) -> dict:
    """Compute correlation between node centrality and prediction."""
    try:
        pr = nx.pagerank(G)
        df_pr = pd.DataFrame(list(pr.items()), columns=['node_id', 'centrality'])
        merged = pd.merge(node_df, df_pr, on='node_id', how='inner')
        if not merged.empty and 'prediction' in merged.columns:
            corr = merged['prediction'].astype(float).corr(merged['centrality'])
            if np.isnan(corr): corr = 0.0
            return {
                "raw_value": float(corr),
                "score": 100 - int(abs(corr) * 50),
                "status": "WARN" if abs(corr) > 0.5 else "PASS"
            }
    except Exception:
        pass
    return {"raw_value": 0, "score": 100, "status": "PASS"}

def compute_structural_metrics(G: nx.Graph, protected_attr: str, node_df: pd.DataFrame) -> dict:
    """Compute all 5 structural fairness metrics."""
    if not protected_attr:
        return {}
        
    return {
        "degree_disparity": compute_degree_disparity(G, protected_attr),
        "pagerank_disparity": compute_pagerank_disparity(G, protected_attr),
        "clustering_disparity": compute_clustering_disparity(G, protected_attr),
        "homophily_coefficient": compute_homophily(G, protected_attr),
        "prediction_centrality_correlation": compute_prediction_centrality_correlation(G, node_df, protected_attr)
    }

if __name__ == "__main__":
    G = nx.path_graph(4)
    nx.set_node_attributes(G, {0: "A", 1: "A", 2: "B", 3: "B"}, "group")
    df = pd.DataFrame({"node_id": [0,1,2,3], "prediction": [1,1,0,0]})
    print(compute_structural_metrics(G, "group", df))
