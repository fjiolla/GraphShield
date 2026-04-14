import torch
import io
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer
from captum.attr import LayerIntegratedGradients

class WhiteBoxAuditor:
    def __init__(self):
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    def _load_resources(self):
        if self.tokenizer is None:
            from transformers import DistilBertTokenizer
            self.tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

    def load_user_model(self, model_bytes: bytes):
        from transformers import DistilBertForSequenceClassification
        model = DistilBertForSequenceClassification.from_pretrained(
            "distilbert-base-uncased", num_labels=2
        )
        buffer = io.BytesIO(model_bytes)
        state_dict = torch.load(buffer, map_location=self.device)
        model.load_state_dict(state_dict)
        model.to(self.device)
        model.eval()
        return model

    async def run_audit(self, model, text: str):
        self._load_resources()
        lig = LayerIntegratedGradients(
            lambda inputs: model(inputs)[0], 
            model.distilbert.embeddings
        )

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(self.device)
        input_ids = inputs["input_ids"]
        baseline_ids = torch.zeros_like(input_ids).to(self.device)


        attributions, delta = lig.attribute(
            inputs=input_ids,
            baselines=baseline_ids,
            target=1,
            return_convergence_delta=True
        )


        attributions = attributions.sum(dim=-1).squeeze(0)
        attributions = attributions / torch.norm(attributions)
        tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0])

        token_scores = [
            {"token": t, "weight_contribution": round(s.item(), 4)}
            for t, s in zip(tokens, attributions)
            if t not in ["[CLS]", "[SEP]", "[PAD]"]
        ]

        return {
            "token_attributions": token_scores,
            "convergence_delta": round(delta.item(), 4)
        }