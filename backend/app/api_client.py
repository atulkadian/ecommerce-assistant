import httpx
from typing import List, Dict, Any
from app.config import get_settings

settings = get_settings()

"""
    Client for interacting with the Fake Store API.
"""
class FakeStoreAPI:
    def __init__(self):
        self.base_url = settings.fake_store_api_url
        
    """
        Fetch all products from the store.
    """
    async def get_products(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/products")
            response.raise_for_status()
            return response.json()
        
    
    """
        Fetch detailed information for a single product.
    """
    async def get_product_details(self, product_id: int) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/products/{product_id}")
            response.raise_for_status()
            return response.json()
    
    """
        Fetch all product categories.
    """
    async def get_categories(self) -> List[str]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/products/categories")
            response.raise_for_status()
            return response.json()
    
    """
        Fetch products by category.
    """
    async def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/products/category/{category}")
            response.raise_for_status()
            return response.json()


fake_store_api = FakeStoreAPI()
