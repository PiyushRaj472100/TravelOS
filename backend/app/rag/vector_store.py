import faiss
import numpy as np


class VectorStore:

    def __init__(self, dimension: int):

        self.dimension = dimension

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.documents = []

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

    def search(
        self,
        vector: list[float],
        top_k: int = 5
    ):

        vector_array = np.array(
            [vector],
            dtype="float32"
        )

        scores, indices = self.index.search(
            vector_array,
            top_k
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