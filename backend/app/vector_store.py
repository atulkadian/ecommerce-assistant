"""
Vector store for semantic product search using FAISS and sentence transformers.
Pre-computes embeddings for all products to enable semantic search capabilities.
"""
import logging
import warnings
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Suppress transformers warnings during model loading
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', message='.*UNEXPECTED.*')

logger = logging.getLogger(__name__)


class ProductVectorStore:
    """Manages product embeddings and semantic search using FAISS."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the vector store with a sentence transformer model.
        
        Args:
            model_name: HuggingFace model name for embeddings (default: all-MiniLM-L6-v2)
                       This is a lightweight model (80MB) that produces 384-dim embeddings
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.index: Optional[faiss.Index] = None
        self.products: List[Dict] = []
        self.dimension = 384
        
    def build_index(self, products: List[Dict]):
        """Build FAISS index from product list.
        
        Args:
            products: List of product dictionaries with 'title' and 'description' fields
        """
        if not products:
            logger.warning("No products provided to build index")
            return
            
        logger.info(f"Building vector index for {len(products)} products")
        self.products = products
        
        # Create text representations combining title and description
        texts = []
        for product in products:
            title = product.get('title', '')
            description = product.get('description', '')
            category = product.get('category', '')
            # Combine for richer semantic understanding
            text = f"{title}. {description}. Category: {category}"
            texts.append(text)
        
        # Generate embeddings
        embeddings = self.model.encode(texts, show_progress_bar=False)
        embeddings = np.array(embeddings).astype('float32')
        
        # Create FAISS index (using L2 distance)
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings)
        
        logger.info(f"Vector index built successfully with {self.index.ntotal} products")
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Semantic search for products based on query.
        
        Args:
            query: Natural language search query
            top_k: Number of results to return
            
        Returns:
            List of products sorted by semantic similarity
        """
        if not self.index or not self.products:
            logger.warning("Vector index not initialized")
            return []
        
        # Encode query
        query_embedding = self.model.encode([query], show_progress_bar=False)
        query_embedding = np.array(query_embedding).astype('float32')
        
        # Search in FAISS index
        distances, indices = self.index.search(query_embedding, min(top_k, len(self.products)))
        
        # Return products sorted by similarity (lower distance = more similar)
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.products):
                product = self.products[idx].copy()
                product['similarity_score'] = float(distance)
                results.append(product)
        
        logger.info(f"Semantic search for '{query}' returned {len(results)} results")
        return results


# Global vector store instance
_vector_store: Optional[ProductVectorStore] = None


def get_vector_store() -> ProductVectorStore:
    """Get or create the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = ProductVectorStore()
    return _vector_store


def initialize_vector_store(products: List[Dict]):
    """Initialize the vector store with products.
    
    Args:
        products: List of product dictionaries
    """
    store = get_vector_store()
    store.build_index(products)
