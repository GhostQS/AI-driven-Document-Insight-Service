from typing import List, Tuple
from transformers import pipeline

class QAPipeline:
    def __init__(self, qa_model: str = "distilbert-base-cased-distilled-squad", enable_ner: bool = False):
        self.qa = pipeline("question-answering", model=qa_model)
        self.enable_ner = enable_ner
        self.ner = pipeline("ner", grouped_entities=True) if enable_ner else None

    def answer(self, question: str, context: str) -> Tuple[str, List[dict], List[dict]]:
        # For long context, the HF pipeline handles sliding windows internally, but we can keep context reasonable.
        result = self.qa({"question": question, "context": context})
        answer = result.get("answer", "")
        spans = [{"start": result.get("start", 0), "end": result.get("end", 0), "score": float(result.get("score", 0.0))}]

        entities: List[dict] = []
        if self.enable_ner and self.ner:
            entities = self.ner(answer)
            # normalize keys for readability
            entities = [{
                "entity_group": e.get("entity_group"),
                "word": e.get("word"),
                "score": float(e.get("score", 0.0)),
                "start": int(e.get("start", 0)),
                "end": int(e.get("end", 0)),
            } for e in entities]
        return answer, spans, entities
