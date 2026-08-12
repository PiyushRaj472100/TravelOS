from pathlib import Path

import faiss
import numpy as np


class VectorStore:

    def __init__(
        self,
        dimension: int
    ):

        self.dimension = dimension

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.documents = []


    # =================================================
    # Add one vector
    # =================================================

    def add(
        self,
        vector: list[float],
        document
    ):

        vector_array = np.array(
            [vector],
            dtype="float32"
        )

        self.index.add(
            vector_array
        )

        self.documents.append(
            document
        )


    # =================================================
    # Add multiple vectors
    # =================================================

    def add_batch(
        self,
        vectors: list[list[float]],
        documents: list
    ):

        if not vectors:
            return

        if len(vectors) != len(documents):

            raise ValueError(
                "Number of vectors must match "
                "number of documents."
            )


        vector_array = np.array(
            vectors,
            dtype="float32"
        )

        self.index.add(
            vector_array
        )

        self.documents.extend(
            documents
        )


    # =================================================
    # Search
    # =================================================

    def search(
        self,
        vector: list[float],
        top_k: int = 5
    ):

        if self.index.ntotal == 0:
            return []


        vector_array = np.array(
            [vector],
            dtype="float32"
        )


        actual_k = min(
            top_k,
            self.index.ntotal
        )


        scores, indices = (
            self.index.search(
                vector_array,
                actual_k
            )
        )


        results = []


        for score, index in zip(
            scores[0],
            indices[0]
        ):

            if index == -1:
                continue


            results.append({
                "score": float(score),
                "document": self.documents[index]
            })


        return results


    # =================================================
    # Save FAISS index
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

        faiss.write_index(
            self.index,
            str(path)
        )


    # =================================================
    # Load FAISS index
    # =================================================

    def load(
        self,
        path: str
    ):

        path = Path(path)

        if not path.exists():

            raise FileNotFoundError(
                f"FAISS index not found: {path}"
            )


        self.index = faiss.read_index(
            str(path)
        )


    # =================================================
    # Statistics
    # =================================================

    @property
    def size(self) -> int:

        return self.index.ntotal