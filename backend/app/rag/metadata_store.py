import json
from pathlib import Path


class MetadataStore:

    def __init__(self):
        self.documents = []

    def add(self, document):
        self.documents.append(document)

    def get(self, index: int):
        return self.documents[index]

    def all(self):
        return self.documents

    def save(self, path: str):
        data = [
            document.model_dump()
            for document in self.documents
        ]

        Path(path).write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )