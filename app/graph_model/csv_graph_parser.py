"""
CSV Graph parser module.
"""

import networkx as nx
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def detect_node_id_column(nodes_df: pd.DataFrame) -> str:
    """
    Auto-detect which column is the node ID.
    Look for columns named: 'id', 'node_id', 'ID', 'Id'
    If none found, use first column.
    Return the column name.
    """
    cols = nodes_df.columns.tolist()
    candidates = ['id', 'node_id', 'id', 'id']
    for c in cols:
        if c.lower() in candidates:
            return c
    return cols[0] if cols else ""

def detect_edge_columns(edges_df: pd.DataFrame) -> tuple:
    """
    Auto-detect source and target columns.
    Look for: 'source'/'target', 'from'/'to', 'src'/'dst'
    Return (source_col, target_col)
    Raises ValueError if cannot detect.
    """
    cols = [c.lower() for c in edges_df.columns.tolist()]
    real_cols = edges_df.columns.tolist()
    
    pairs = [('source', 'target'), ('from', 'to'), ('src', 'dst')]
    for src, tgt in pairs:
        if src in cols and tgt in cols:
            return real_cols[cols.index(src)], real_cols[cols.index(tgt)]
            
    raise ValueError("Could not auto-detect source and target columns in edges csv.")

def load_csv_graph(nodes_path: str, edges_path: str) -> dict:
    """
    Load graph from two CSV files.
    nodes_path: CSV with at minimum an 'id' column
    edges_path: CSV with 'source' and 'target' columns, 
                optional 'weight' column
    
    Returns same structure as gml_parser.load_gml()
    Raises: FileNotFoundError, ValueError if required columns missing
    """
    try:
        nodes_df = pd.read_csv(nodes_path)
        edges_df = pd.read_csv(edges_path)
    except FileNotFoundError as e:
        logger.error(f"Missing CSV file: {e}")
        raise
    
    if nodes_df.empty or edges_df.empty:
        raise ValueError("Nodes or edges CSV is empty")
        
    id_col = detect_node_id_column(nodes_df)
    src_col, tgt_col = detect_edge_columns(edges_df)
    
    G = nx.Graph()
    # Add nodes with logic
    for _, row in nodes_df.iterrows():
        node_id = row[id_col]
        attrs = row.drop(labels=[id_col]).to_dict()
        G.add_node(node_id, **attrs)
        
    # Add edges
    for _, row in edges_df.iterrows():
        src = row[src_col]
        tgt = row[tgt_col]
        attrs = row.drop(labels=[src_col, tgt_col]).to_dict()
        G.add_edge(src, tgt, **attrs)
        
    from app.graph_model.gml_parser import extract_node_attribute_names, extract_edge_attribute_names
    
    return {
        "graph": G,
        "node_attributes": extract_node_attribute_names(G),
        "edge_attributes": extract_edge_attribute_names(G),
        "is_directed": False, # Basic parser
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "format": "csv"
    }

def handle_single_csv_format(file_path: str) -> dict:
    """
    Handle case where user uploads ONE csv with columns:
    source, target, source_attr_1, target_attr_1, ...
    Convert this format to NetworkX graph.
    """
    df = pd.read_csv(file_path)
    src_col, tgt_col = detect_edge_columns(df)
    
    G = nx.Graph()
    for _, row in df.iterrows():
        src = row[src_col]
        tgt = row[tgt_col]
        edge_attrs = row.drop(labels=[src_col, tgt_col]).to_dict()
        G.add_edge(src, tgt, **edge_attrs)
        
    from app.graph_model.gml_parser import extract_node_attribute_names, extract_edge_attribute_names
    return {
        "graph": G,
        "node_attributes": extract_node_attribute_names(G),
        "edge_attributes": extract_edge_attribute_names(G),
        "is_directed": False,
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "format": "csv"
    }

if __name__ == "__main__":
    import os, tempfile
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode='w') as fn:
        fn.write("id,age\n1,30\n2,25\n")
        f_n = fn.name
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode='w') as fe:
        fe.write("source,target,weight\n1,2,5\n")
        f_e = fe.name
    
    try:
        res = load_csv_graph(f_n, f_e)
        print("CSV Graph output:", res.keys(), "Nodes:", res['node_count'])
    finally:
        os.remove(f_n)
        os.remove(f_e)
