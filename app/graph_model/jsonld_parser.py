"""
JSON-LD parser module.
"""

import networkx as nx
import json
import logging

logger = logging.getLogger(__name__)

def clean_jsonld_key(key: str) -> str:
    """
    Remove @, namespace prefixes, URLs from JSON-LD keys.
    Example: "http://schema.org/name" -> "name"
    Example: "@type" -> "type"
    """
    if key.startswith("@"):
        return key[1:]
    if "/" in key:
        return key.split("/")[-1]
    if ":" in key:
        return key.split(":")[-1]
    return key

def flatten_nested_entity(entity: dict, prefix: str = "") -> dict:
    """
    Flatten nested JSON-LD entity into flat dict.
    Example: {"name": "John", "address": {"city": "Mumbai"}}
    Becomes: {"name": "John", "address_city": "Mumbai"}
    """
    items = []
    for k, v in entity.items():
        clean_k = clean_jsonld_key(k)
        new_key = f"{prefix}_{clean_k}" if prefix else clean_k
        if isinstance(v, dict):
            items.extend(flatten_nested_entity(v, new_key).items())
        elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
            pass # Skipping deeply nested list of dicts for simple graph representation
        else:
            items.append((new_key, v))
    return dict(items)

def extract_entities_from_jsonld(data: dict) -> list:
    """
    Extract all entities from @graph array.
    Each entity becomes a node.
    Return list of dicts: [{"@id": ..., "attr1": ..., ...}]
    """
    if "@graph" in data:
        entities = data["@graph"]
    elif isinstance(data, list):
        entities = data
    else:
        entities = [data]
        
    flattened = []
    for ent in entities:
        if isinstance(ent, dict) and "@id" in ent:
            flat = flatten_nested_entity(ent)
            # Ensure "id" maps to original "@id"
            flat["id"] = ent["@id"]
            flattened.append(flat)
    return flattened

def extract_relationships_as_edges(entities: list) -> list:
    """
    Find keys in entities whose values reference other @id values.
    These become edges.
    Return list of (source_id, target_id, relationship_type) tuples.
    """
    edges = []
    all_ids = {e.get("id") for e in entities if e.get("id")}
    
    for ent in entities:
        src = ent.get("id")
        if not src:
            continue
        for k, v in ent.items():
            if k == "id":
                continue
            if isinstance(v, str) and v in all_ids:
                edges.append((src, v, k))
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, str) and item in all_ids:
                        edges.append((src, item, k))
    return edges

def load_jsonld(file_path: str) -> dict:
    """
    Parse JSON-LD file into NetworkX graph.
    
    Returns same structure as gml_parser.load_gml()
    with format="jsonld"
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSONLD {file_path}: {e}")
        raise ValueError(f"Invalid JSONLD: {e}")
        
    entities = extract_entities_from_jsonld(data)
    edges = extract_relationships_as_edges(entities)
    
    G = nx.Graph()
    for ent in entities:
        node_id = ent.pop("id")
        G.add_node(node_id, **ent)
        
    for src, tgt, rel in edges:
        G.add_edge(src, tgt, relationship=rel)
        
    from app.graph_model.gml_parser import extract_node_attribute_names, extract_edge_attribute_names
    return {
        "graph": G,
        "node_attributes": extract_node_attribute_names(G),
        "edge_attributes": extract_edge_attribute_names(G),
        "is_directed": False,
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "format": "jsonld"
    }

if __name__ == "__main__":
    import os, tempfile
    test_data = {
        "@graph": [
            {"@id": "node1", "@type": "Person", "name": "Alice", "knows": "node2"},
            {"@id": "node2", "@type": "Person", "name": "Bob"}
        ]
    }
    with tempfile.NamedTemporaryFile(suffix=".jsonld", delete=False, mode='w') as fn:
        json.dump(test_data, fn)
        f_n = fn.name
    try:
        res = load_jsonld(f_n)
        print("JSONLD Graph nodes:", res["node_count"], "edges:", res["edge_count"])
    finally:
        os.remove(f_n)
