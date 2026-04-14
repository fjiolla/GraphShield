"""
GML parser module for loading and returning NetworkX graphs.
"""

import networkx as nx
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def load_gml(file_path: str) -> dict:
    """
    Load a GML file and return graph + metadata.
    
    Returns:
    {
        "graph": nx.Graph object,
        "node_attributes": list of attribute names found on nodes,
        "edge_attributes": list of attribute names found on edges,
        "is_directed": bool,
        "node_count": int,
        "edge_count": int,
        "format": "gml"
    }
    Raises: FileNotFoundError, ValueError if file is invalid GML
    """
    try:
        G = nx.read_gml(file_path)
    except Exception as e:
        logger.error(f"Failed to read GML file {file_path}: {e}")
        raise ValueError(f"Invalid GML file: {e}")
    
    node_attrs = extract_node_attribute_names(G)
    edge_attrs = extract_edge_attribute_names(G)
    
    return {
        "graph": G,
        "node_attributes": node_attrs,
        "edge_attributes": edge_attrs,
        "is_directed": G.is_directed(),
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "format": "gml"
    }

def extract_node_attribute_names(G: nx.Graph) -> list:
    """Return list of all unique attribute keys across all nodes."""
    attrs = set()
    for _, data in G.nodes(data=True):
        attrs.update(data.keys())
    return list(attrs)

def extract_edge_attribute_names(G: nx.Graph) -> list:
    """Return list of all unique attribute keys across all edges."""
    attrs = set()
    for _, _, data in G.edges(data=True):
        attrs.update(data.keys())
    return list(attrs)

def get_node_dataframe(G: nx.Graph) -> pd.DataFrame:
    """
    Convert all node attributes into a pandas DataFrame.
    One row per node, one column per attribute.
    Include 'node_id' as first column.
    """
    nodes_data = []
    for n, data in G.nodes(data=True):
        node_dict = {'node_id': n}
        node_dict.update(data)
        nodes_data.append(node_dict)
    
    df = pd.DataFrame(nodes_data)
    # Ensure node_id is at the front
    if not df.empty and 'node_id' in df.columns:
        cols = ['node_id'] + [c for c in df.columns if c != 'node_id']
        df = df[cols]
    return df

if __name__ == "__main__":
    # Smoke test
    import os
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix=".gml", delete=False, mode='w') as f:
        f.write('graph [ node [ id 1 label "node1" age 30 ] node [ id 2 label "node2" age 25 ] edge [ source 1 target 2 ] ]')
        tmp_name = f.name
    
    try:
        res = load_gml(tmp_name)
        print("GML Load keys:", res.keys())
        df = get_node_dataframe(res["graph"])
        print("Node DF shapes:", df.shape)
    finally:
        os.remove(tmp_name)
