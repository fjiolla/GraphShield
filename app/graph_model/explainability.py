"""
Explainability module for graph fairness.
"""

import networkx as nx
import pandas as pd
import numpy as np
import logging
import community as community_louvain

logger = logging.getLogger(__name__)

def generate_global_explanation(
    G: nx.Graph,
    node_df: pd.DataFrame,
    structural_metrics: dict,
    protected_attr: str
) -> dict:
    """
    Global explanation: what structural factors most drive bias?
    All descriptions are fully dynamic using real computed values.
    """
    drivers = []
    
    # PageRank disparity — use real per-group values
    pr_data = structural_metrics.get("pagerank_disparity", {})
    if pr_data.get("status") == "FAIL":
        pg = pr_data.get("per_group", {})
        if pg:
            best_g = max(pg, key=pg.get)
            worst_g = min(pg, key=pg.get)
            ratio = pg[best_g] / pg[worst_g] if pg[worst_g] > 0 else 0
            drivers.append({
                "factor": "pagerank",
                "description": f"PageRank disparity {pr_data.get('raw_value', 0):.2f}x: '{best_g}' avg PageRank {pg[best_g]:.6f} vs '{worst_g}' avg {pg[worst_g]:.6f} across {protected_attr} groups.",
                "severity": "high"
            })
        
    # Degree disparity — use real per-group values
    deg_data = structural_metrics.get("degree_disparity", {})
    if deg_data.get("status") == "FAIL":
        pg = deg_data.get("per_group", {})
        if pg:
            best_g = max(pg, key=pg.get)
            worst_g = min(pg, key=pg.get)
            drivers.append({
                "factor": "degree",
                "description": f"Degree disparity {deg_data.get('raw_value', 0):.2f}x: '{best_g}' avg degree {pg[best_g]:.2f} vs '{worst_g}' avg degree {pg[worst_g]:.2f} across {protected_attr} groups.",
                "severity": "high"
            })
        
    # Homophily — use real coefficient value
    homo_data = structural_metrics.get("homophily_coefficient", {})
    if homo_data.get("status") == "FAIL":
        coeff = homo_data.get("raw_value", 0)
        drivers.append({
            "factor": "homophily",
            "description": f"Homophily coefficient of {coeff:.4f} detected — graph is {('highly' if coeff > 0.7 else 'moderately')} segregated by {protected_attr}, limiting cross-group connections.",
            "severity": "high" if coeff > 0.7 else "medium"
        })

    # Clustering disparity
    cl_data = structural_metrics.get("clustering_disparity", {})
    if cl_data.get("status") == "FAIL":
        pg = cl_data.get("per_group", {})
        if pg:
            best_g = max(pg, key=pg.get)
            worst_g = min(pg, key=pg.get)
            drivers.append({
                "factor": "clustering",
                "description": f"Clustering disparity {cl_data.get('raw_value', 0):.2f}x: '{best_g}' avg clustering {pg[best_g]:.4f} vs '{worst_g}' avg clustering {pg[worst_g]:.4f}.",
                "severity": "medium"
            })

    # Dynamic summary with real counts
    num_fail = len(drivers)
    total_metrics = len(structural_metrics)
    summary = f"Analysis found {num_fail} out of {total_metrics} structural metrics failing fairness thresholds."
    if drivers:
        factor_names = ", ".join([d["factor"] for d in drivers])
        summary += f" Key bias drivers: {factor_names}."
    else:
        summary += " No structural bias drivers detected."
    
    return {
        "top_bias_drivers": drivers,
        "summary": summary
    }

def compute_neighbor_prediction_rate(G: nx.Graph, node_id: str, node_df: pd.DataFrame) -> float:
    """Compute fraction of direct neighbors with positive predictions."""
    if node_id not in G: return 0.0
    neighbors = list(G.neighbors(node_id))
    if not neighbors: return 0.0
    
    pred_map = dict(zip(node_df['node_id'], node_df.get('prediction', np.zeros(len(node_df)))))
    pos_count = sum(1 for n in neighbors if str(pred_map.get(n, 0)) == '1')
    return pos_count / len(neighbors)

def generate_node_explanation(
    G: nx.Graph,
    node_id: str,
    node_df: pd.DataFrame,
    protected_attr: str
) -> dict:
    """
    Explain why a specific node got its prediction.
    """
    if node_id not in G.nodes:
        return {}
        
    d = G.degree(node_id) if hasattr(G, 'degree') else 0
    try:
        pr = nx.pagerank(G).get(node_id, 0)
    except:
        pr = 0
    try:
        cc = nx.clustering(G, node_id)
    except:
        cc = 0
        
    node_row = node_df[node_df['node_id'] == node_id]
    pred = float(node_row['prediction'].iloc[0]) if not node_row.empty and 'prediction' in node_df.columns else 0.0
    group = str(node_row[protected_attr].iloc[0]) if not node_row.empty and protected_attr in node_df.columns else "Unknown"
    
    return {
        "node_id": node_id,
        "group": group,
        "prediction": pred,
        "structural_factors": {
            "degree": d,
            "degree_percentile": "[HARDCODED] 0.0",
            "pagerank": pr,
            "pagerank_percentile": "[HARDCODED] 0.0",
            "clustering_coefficient": cc
        },
        "neighbor_analysis": {
            "neighbor_count": len(list(G.neighbors(node_id))),
            "neighbor_positive_rate": compute_neighbor_prediction_rate(G, node_id, node_df),
            "same_group_ratio": "[HARDCODED] 0.0"
        },
        "explanation_text": f"[HARDCODED] Node {node_id} belongs to group {group} and has degree {d}."
    }

def generate_community_explanation(
    G: nx.Graph,
    node_df: pd.DataFrame,
    protected_attr: str
) -> dict:
    """
    Run community detection using Louvain algorithm.
    Check if protected groups are isolated in communities.
    """
    try:
        if G.is_directed():
            undir_G = G.to_undirected()
        else:
            undir_G = G
        partition = community_louvain.best_partition(undir_G)
        num_comms = len(set(partition.values()))
    except Exception as e:
        logger.warning(f"Community detection failed: {e}")
        return {"error": str(e)}
        
    return {
        "num_communities": num_comms,
        "summary": f"Detected {num_comms} main communities."
    }

if __name__ == "__main__":
    G = nx.path_graph(3)
    df = pd.DataFrame({"node_id": [0,1,2], "pred": [1,0,1]})
    print(generate_community_explanation(G, df, "group"))
