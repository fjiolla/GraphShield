import asyncio
from app.graph_model.pipeline import run_graph_bias_pipeline

res = run_graph_bias_pipeline(
    graph_file_path="test_graph.gml",
    file_format="gml",
    protected_attr="gender",
    prediction_source="csv",
    predictions_csv_path="test_preds.csv",
    prediction_col="",
    ground_truth_col="",
    domain="test"
)
print(res)
