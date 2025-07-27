from typing import List, Dict, Tuple
from google.cloud import aiplatform
import logging
from google.cloud import aiplatform_v1
from google.cloud.aiplatform_v1 import MatchServiceClient, FindNeighborsRequest
import os

logger = logging.getLogger(__name__)

VECTOR_INDEX_ID = os.getenv("RL_VECTOR_INDEX_ID")
ENDPOINT_ID = os.getenv("RL_ENDPOINT_ID")


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Uses Vertex AI embedding model to get vector representations for texts.
    """
    model = aiplatform.TextEmbeddingModel.from_pretrained("textembedding-gecko@latest")
    embeddings = model.get_embeddings(texts)
    return [e.values for e in embeddings]


def upsert_to_index(documents: List[Dict]):
    """
    Upserts documents to the Vertex AI vector index.
    """
    client = aiplatform_v1.IndexServiceClient()
    index_resource = client.index_path(
        project=aiplatform.init().project,
        location=aiplatform.init().location,
        index=VECTOR_INDEX_ID,
    )

    # Prepare datapoints for upsert
    datapoints = []
    for doc in documents:
        datapoint = aiplatform_v1.IndexDatapoint(
            datapoint_id=doc["id"],
            feature_vector=doc["embedding"],
            restricts=[
                aiplatform_v1.IndexDatapoint.Restrict(namespace=k, allow=[str(v)])
                for k, v in doc.get("metadata", {}).items()
            ],
        )
        datapoints.append(datapoint)

    logger.info(f"Upserting {len(datapoints)} datapoints to index {VECTOR_INDEX_ID}")

    upsert_request = aiplatform_v1.UpsertDatapointsRequest(
        index=index_resource, datapoints=datapoints
    )
    client.upsert_datapoints(request=upsert_request)


def search_index(embedding: List[float], filter: str, top_k: int) -> List[Dict]:
    """
    Searches the Vertex AI vector index for similar items.
    """
    client = MatchServiceClient()
    endpoint = client.match_service_path(
        project=aiplatform.init().project,
        location=aiplatform.init().location,
        deployed_index_id=ENDPOINT_ID,
    )

    query = {
        "embedding": embedding,
        "filter": filter,
    }

    request = FindNeighborsRequest(
        index_endpoint=endpoint,
        queries=[query],
        num_neighbors=top_k,
    )

    response = client.find_neighbors(request=request)
    results = []
    for neighbor in response.nearest_neighbors[0].neighbors:
        results.append(
            {
                "id": neighbor.datapoint.datapoint_id,
                "score": neighbor.distance,
                "metadata": dict(neighbor.datapoint.restricts),
            }
        )
    return results


def add_user_data(user_id: str, receipt_data: str):
    """
    Adds a single receipt data for a user to the Vertex AI vector index.
    The receipt is embedded and stored with user_id metadata.
    """
    embedding = get_embeddings([receipt_data])[0]
    document = {
        "id": f"{user_id}",
        "embedding": embedding,
        "metadata": {"user_id": user_id, "receipt": receipt_data},
    }
    upsert_to_index([document])


def retrieve_context(user_id: str, query: str, top_k: int = 5) -> List[Dict]:
    """
    Retrieves the most relevant receipts for a user based on the query.
    """
    query_embedding = get_embeddings([query])[0]
    filter_str = f"user_id:{user_id}"
    results = search_index(query_embedding, filter=filter_str, top_k=top_k)
    return results


# tools for relevancy
class SimpleRAGAgent:
    def __init__(self, file_path: str = "rag_data.txt"):
        """
        Initialize the RAG agent with a file path for data storage.

        Args:
            file_path (str): Path to the text file for storing data
        """
        self.file_path = file_path
        self.ensure_file_exists()

    def ensure_file_exists(self):
        """Ensure the data file exists, create if it doesn't."""
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                pass  # Create empty file

    def add_data(self, user_id: str, data: str):
        """
        Add data for a specific user to the text file.
        Format: user_id followed by their data on the same line.

        Args:
            user_id (str): Unique identifier for the user
            data (str): Data content to store
        """
        # Clean the data to ensure it doesn't contain newlines that would break our format
        cleaned_data = data.replace("\n", " ").replace("\r", " ").strip()

        # Format: user_id data_content
        line = f"{user_id} {cleaned_data}\n"

        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(line)

        print(f"Added data for user {user_id}")

    def filter_data_by_user_id(self, user_id: str) -> List[str]:
        """
        Filter and retrieve all data entries for a specific user ID.

        Args:
            user_id (str): User ID to filter by

        Returns:
            List[str]: List of data entries for the specified user
        """
        user_data = []

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        # Split only on the first space to separate user_id from data
                        parts = line.split(" ", 1)
                        if len(parts) >= 2 and parts[0] == user_id:
                            user_data.append(parts[1])
        except FileNotFoundError:
            print(f"File {self.file_path} not found")
            return []

        return user_data

    def simple_rag_search(
        self, query: str, user_id: str = None, top_k: int = 5
    ) -> List[Tuple[str, str, float]]:
        """
        Perform a simple RAG search using basic keyword matching and scoring.

        Args:
            query (str): Search query
            user_id (str, optional): Filter by specific user ID
            top_k (int): Number of top results to return

        Returns:
            List[Tuple[str, str, float]]: List of tuples (user_id, content, score)
        """
        # Normalize query for better matching
        query_words = set(query.lower().split())
        results = []

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        # Split only on the first space
                        parts = line.split(" ", 1)
                        if len(parts) >= 2:
                            current_user_id, content = parts[0], parts[1]

                            # If user_id filter is specified, skip non-matching entries
                            if user_id and current_user_id != user_id:
                                continue

                            # Calculate simple relevance score based on keyword overlap
                            content_words = set(content.lower().split())
                            common_words = query_words.intersection(content_words)

                            if (
                                common_words
                            ):  # Only include results with at least one matching word
                                # Simple scoring: ratio of matching words
                                score = len(common_words) / len(query_words)
                                # Boost score if query is a substring of content
                                if query.lower() in content.lower():
                                    score += 0.5

                                results.append((current_user_id, content, score))

        except FileNotFoundError:
            print(f"File {self.file_path} not found")
            return []

        # Sort by score in descending order and return top_k results
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]

    def get_all_data(self) -> Dict[str, List[str]]:
        """
        Retrieve all data organized by user ID.

        Returns:
            Dict[str, List[str]]: Dictionary with user_ids as keys and lists of their data as values
        """
        all_data = defaultdict(list)

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        parts = line.split(" ", 1)
                        if len(parts) >= 2:
                            user_id, content = parts[0], parts[1]
                            all_data[user_id].append(content)
        except FileNotFoundError:
            print(f"File {self.file_path} not found")
            return {}

        return dict(all_data)

    def clear_data(self):
        """Clear all data from the file."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            pass  # Clear file
        print("All data cleared")


def get_relevant_context(user_id: str, query: str) -> str:
    """
    this is the 'get_relevant_context' tool
    this function is used to retrieve relevant context for a user reciepts or text
    Args:
        user_id (str): The ID of the user.
        query (str): The text given by the user as a part of the chat.
    Returns:
        str: The relevant context retrieved from the vector index.
    """
    rag = SimpleRAGAgent("data/rag_data.txt")
    search_results = rag.simple_rag_search("machine learning", top_k=3)
    search_results = rag.simple_rag_search("programming", user_id="user2", top_k=5)
    context = ""
    for i, (user_id, content, score) in enumerate(search_results, 1):
        context += content + "\n"
    return context


def put_relevent_data(user_id: str, data: str) -> str:
    """
    Adds a new receipt data for a user to the vector index.
    Args:
        user_id (str): The ID of the user.
        data (str): The data to be added.
    Returns:
        str: Confirmation message.
    """
    rag = SimpleRAGAgent("data/rag_data.txt")
    rag.add_data(user_id, data)
    return "data added successfully"
