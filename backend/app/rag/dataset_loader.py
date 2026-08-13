import json
from pathlib import Path

from app.rag.document import RAGDocument


class RAGDatasetLoader:

    def __init__(
        self,
        dataset_path: str | None = None
    ):

        # ---------------------------------------------
        # Find backend directory
        # ---------------------------------------------

        backend_dir = Path(
            __file__
        ).resolve().parents[2]

        if dataset_path is None:

            self.dataset_path = (
                backend_dir
                / "data"
                / "travel_knowledge"
            )

        else:

            self.dataset_path = Path(
                dataset_path
            ).resolve()


    def load_documents(
        self
    ) -> list[RAGDocument]:

        documents = []

        print(
            "Loading RAG dataset from:"
        )

        print(
            self.dataset_path
        )


        # ---------------------------------------------
        # Check dataset directory
        # ---------------------------------------------

        if not self.dataset_path.exists():

            raise FileNotFoundError(
                "RAG dataset directory not found: "
                f"{self.dataset_path}"
            )


        # ---------------------------------------------
        # Find JSON files
        # ---------------------------------------------

        json_files = sorted(
            self.dataset_path.glob("*.json")
        )

        print(
            f"Found {len(json_files)} JSON files."
        )


        # ---------------------------------------------
        # Process each country
        # ---------------------------------------------

        for file_path in json_files:

            # Ignore index.json

            if file_path.name == "index.json":
                continue


            print(
                f"Loading: {file_path.name}"
            )


            data = json.loads(
                file_path.read_text(
                    encoding="utf-8"
                )
            )


            # -----------------------------------------
            # Process documents inside JSON
            # -----------------------------------------

            for item in data:

                # =====================================
                # Category-specific source
                # =====================================

                category_source = item.get(
                    "category_source",
                    {}
                )

                source_url = (
                    category_source.get("url")
                )


                # =====================================
                # Browser fallback
                # =====================================

                fallback_search = item.get(
                    "fallback_search",
                    {}
                )

                fallback_search_url = (
                    fallback_search.get("url")
                )


                # =====================================
                # Create RAGDocument
                # =====================================

                document = RAGDocument(

                    # ---------------------------------
                    # Main content
                    # ---------------------------------

                    text=item["text"],


                    # ---------------------------------
                    # Geographic metadata
                    # ---------------------------------

                    country=item.get(
                        "country"
                    ),

                    region=item.get(
                        "region"
                    ),

                    city=item.get(
                        "city"
                    ),


                    # ---------------------------------
                    # Category
                    # ---------------------------------

                    category=item.get(
                        "category"
                    ),


                    # ---------------------------------
                    # Source
                    # ---------------------------------

                    source=item.get(
                        "source"
                    ),

                    # IMPORTANT:
                    # Use the URL extracted from
                    # category_source

                    source_url=source_url,


                    # ---------------------------------
                    # Title
                    # ---------------------------------

                    title=item.get(
                        "title"
                    ),


                    # ---------------------------------
                    # Document ID
                    # ---------------------------------

                    document_id=item.get(
                        "document_id"
                    ),


                    # ---------------------------------
                    # Browser fallback URL
                    # ---------------------------------

                    fallback_search_url=(
                        fallback_search_url
                    )
                )


                documents.append(
                    document
                )


        # ---------------------------------------------
        # Final result
        # ---------------------------------------------

        print(
            f"Loaded {len(documents)} documents."
        )

        return documents