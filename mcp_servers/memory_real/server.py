#!/usr/bin/env python3
"""
Real Qdrant Memory MCP Server (Native FastMCP)

This MCP server provides long-term memory (RAG) for incident correlation.
Uses standard mcp.server.fastmcp implementation.
"""

import json
import logging
import os
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from fastembed import TextEmbedding
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    QdrantClient = None
    TextEmbedding = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Collection name for incidents
INCIDENTS_COLLECTION = "sre_incidents"

# Initialize Qdrant client and embedding model
qdrant_client = None
embedding_model = None


def initialize_qdrant():
    """Initialize Qdrant client and embedding model."""
    global qdrant_client, embedding_model

    if not QDRANT_AVAILABLE:
        logger.warning("⚠️ Qdrant dependencies not installed. Memory will not work.")
        logger.warning("⚠️ Install with: pip install qdrant-client fastembed")
        return

    # Get Qdrant URL
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")

    try:
        # Initialize Qdrant client
        qdrant_client = QdrantClient(url=qdrant_url, timeout=10)

        # Test connection
        qdrant_client.get_collections()
        logger.info(f"✅ Connected to Qdrant at {qdrant_url}")

        # Initialize embedding model
        embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        logger.info("✅ Initialized embedding model")

        # Ensure collection exists
        collections = qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if INCIDENTS_COLLECTION not in collection_names:
            # Create collection
            qdrant_client.create_collection(
                collection_name=INCIDENTS_COLLECTION,
                vectors_config=VectorParams(
                    size=384,  # bge-small-en-v1.5 embedding size
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"✅ Created collection: {INCIDENTS_COLLECTION}")
        else:
            logger.info(f"✅ Collection exists: {INCIDENTS_COLLECTION}")

    except Exception as e:
        logger.error(f"❌ Failed to initialize Qdrant: {e}")
        qdrant_client = None


# Initialize on import
try:
    initialize_qdrant()
except Exception as e:
    logger.warning(f"⚠️ Qdrant initialization failed: {e}")


# Initialize FastMCP server
port = int(os.getenv("HTTP_PORT", "3000"))
host = os.getenv("HOST", "0.0.0.0")

mcp = FastMCP("Qdrant Memory", host=host, port=port)


@mcp.tool()
def store_incident_memory(
    incident_text: str,
    incident_id: str,
    metadata: Optional[str] = None,
) -> str:
    """
    Store an incident in the memory store for future recall.
    
    Args:
        incident_text: Text description of the incident and resolution
        incident_id: Unique identifier for the incident
        metadata: Additional metadata as JSON string (optional)
    
    Returns:
        JSON string with storage result
    """
    if not qdrant_client or not embedding_model:
        return json.dumps({"error": "Qdrant client not initialized. Set QDRANT_URL environment variable."})

    logger.info(f"Storing incident in memory: {incident_id}")

    try:
        # Parse metadata if provided
        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                logger.warning(f"Invalid metadata JSON, ignoring: {metadata}")

        # Generate embedding
        embeddings = list(embedding_model.embed([incident_text]))
        embedding = embeddings[0].tolist()

        # Prepare payload
        payload = metadata_dict.copy()
        payload["incident_text"] = incident_text
        payload["incident_id"] = incident_id

        # Store in Qdrant
        point = PointStruct(
            id=hash(incident_id) % (2**63),  # Convert to int64
            vector=embedding,
            payload=payload,
        )

        qdrant_client.upsert(
            collection_name=INCIDENTS_COLLECTION,
            points=[point],
        )

        logger.info(f"✅ Stored incident in memory: {incident_id}")
        return json.dumps({"status": "success", "incident_id": incident_id})

    except Exception as e:
        logger.error(f"❌ Failed to store incident: {e}")
        return json.dumps({"error": f"Failed to store incident: {str(e)}"})


@mcp.tool()
def recall_similar_incidents(
    query_text: str,
    limit: int = 5,
    score_threshold: float = 0.7,
) -> str:
    """
    Search for similar past incidents using semantic similarity.
    
    Args:
        query_text: Query text (e.g., alert context, incident description)
        limit: Maximum number of results (1-20)
        score_threshold: Minimum similarity score (0.0-1.0)
    
    Returns:
        JSON string with similar incidents
    """
    if not qdrant_client or not embedding_model:
        return json.dumps({"error": "Qdrant client not initialized. Set QDRANT_URL environment variable."})

    logger.info(f"Searching for similar incidents: {query_text[:50]}...")

    try:
        # Generate query embedding
        embeddings = list(embedding_model.embed([query_text]))
        query_embedding = embeddings[0].tolist()

        # Search in Qdrant
        search_results = qdrant_client.search(
            collection_name=INCIDENTS_COLLECTION,
            query_vector=query_embedding,
            limit=min(max(limit, 1), 20),  # Clamp between 1 and 20
            score_threshold=max(0.0, min(1.0, score_threshold)),  # Clamp between 0.0 and 1.0
        )

        # Format results
        results = []
        for result in search_results:
            results.append({
                "incident_id": result.payload.get("incident_id", "unknown"),
                "incident_text": result.payload.get("incident_text", ""),
                "similarity_score": result.score,
                "metadata": {
                    k: v
                    for k, v in result.payload.items()
                    if k not in ["incident_id", "incident_text"]
                },
            })

        logger.info(f"✅ Found {len(results)} similar incidents")
        return json.dumps({"results": results, "count": len(results)}, indent=2)

    except Exception as e:
        logger.error(f"❌ Failed to search incidents: {e}")
        return json.dumps({"error": f"Failed to search incidents: {str(e)}"})


if __name__ == "__main__":
    logger.info(f"Starting Qdrant Memory MCP Server on {host}:{port}")
    mcp.run(transport="sse")
