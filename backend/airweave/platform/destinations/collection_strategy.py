"""Physical collection naming for Qdrant multi-tenancy.

All collections now use shared physical collections in Qdrant:
- 384-dim vectors → airweave_shared_minilm_l6_v2 (local model)
- 1536-dim vectors → airweave_shared_text_embedding_3_small (OpenAI)
- 3072-dim vectors → airweave_shared_text_embedding_3_large (OpenAI)

Tenant isolation is achieved via airweave_collection_id payload filtering.
"""

from airweave.core.config import settings


def get_default_vector_size() -> int:
    """Auto-detect vector size based on embedding model configuration.

    Priority order:
        1. EMBEDDING_DIM if explicitly set (for custom models)
        2. 3072 if OpenAI API key is set (text-embedding-3-large)
        3. 384 otherwise (MiniLM-L6-v2)

    Returns:
        Vector dimension size for embedding model
    """
    # Check for explicit dimension override first
    if settings.EMBEDDING_DIM is not None:
        return settings.EMBEDDING_DIM

    # Fall back to API key-based detection
    return 3072 if settings.OPENAI_API_KEY else 384


def get_physical_collection_name(vector_size: int | None = None) -> str:
    """Get physical Qdrant collection name based on vector size.

    Args:
        vector_size: Vector dimensions. Auto-detected if None.

    Returns:
        Physical collection name in Qdrant:
        - "airweave_shared_text_embedding_3_large" for 3072-dim vectors
        - "airweave_shared_text_embedding_3_small" for 1536-dim vectors
        - "airweave_shared_minilm_l6_v2" for 384-dim vectors
        - "airweave_shared_custom_{dim}" for other dimensions (custom models)
    """
    if vector_size is None:
        vector_size = get_default_vector_size()

    if vector_size == 3072:
        return "airweave_shared_text_embedding_3_large"
    elif vector_size == 1536:
        return "airweave_shared_text_embedding_3_small"
    elif vector_size == 384:
        return "airweave_shared_minilm_l6_v2"
    else:
        # Custom dimension - use generic naming
        return f"airweave_shared_custom_{vector_size}"


def get_openai_embedding_model_for_vector_size(vector_size: int) -> str:
    """Get OpenAI embedding model name for given vector dimensions.

    Supports custom model override via EMBEDDING_MODEL environment variable.
    If EMBEDDING_MODEL is set, it takes precedence over dimension-based selection.

    Args:
        vector_size: Vector dimensions (3072 or 1536)

    Returns:
        - Custom model from EMBEDDING_MODEL if set (always takes precedence)
        - "text-embedding-3-large" for 3072-dim (default)
        - "text-embedding-3-small" for 1536-dim (default)

    Raises:
        ValueError: For vector sizes that don't use OpenAI models (e.g., 384 uses local model)
    """
    # Check for custom override first (always takes precedence)
    if settings.EMBEDDING_MODEL:
        return settings.EMBEDDING_MODEL

    # Fall back to dimension-based selection
    if vector_size == 3072:
        return "text-embedding-3-large"
    elif vector_size == 1536:
        return "text-embedding-3-small"
    else:
        raise ValueError(
            f"No OpenAI model for vector_size {vector_size}. Only 3072 and 1536 use OpenAI models."
        )
