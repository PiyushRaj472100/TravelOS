import json
from pathlib import Path

from app.rag.document import RAGDocument


class MetadataStore:

    def __init__(self):

        self.documents = []


    # =================================================
    # Add one document
    # =================================================

    def add(
        self,
        document: RAGDocument
    ):

        self.documents.append(
            document
        )


    # =================================================
    # Add multiple documents
    # =================================================

    def add_batch(
        self,
        documents: list[RAGDocument]
    ):

        self.documents.extend(
            documents
        )


    # =================================================
    # Get document
    # =================================================

    def get(
        self,
        index: int
    ) -> RAGDocument:

        return self.documents[index]


    # =================================================
    # Get all documents
    # =================================================

    def all(self) -> list[RAGDocument]:

        return self.documents


    # =================================================
    # Count documents
    # =================================================

    def count(self) -> int:

        return len(
            self.documents
        )


    # =================================================
    # Save metadata
    # =================================================

    def save(
        self,
        path: str
    ):

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        data = [
            document.model_dump(
                mode="json"
            )
            for document in self.documents
        ]

        path.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )


    # =================================================
    # Load metadata
    # =================================================

    def load(
        self,
        path: str
    ):

        path = Path(path)

        if not path.exists():

            raise FileNotFoundError(
                f"Metadata file not found: {path}"
            )


        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )


        self.documents = [
            RAGDocument.model_validate(
                item
            )
            for item in data
        ]