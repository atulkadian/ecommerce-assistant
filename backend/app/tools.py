from langchain_core.tools import tool
from app.api_client import fake_store_api
from typing import Optional, List

user_carts = {}


def get_user_cart(user_id: str = "default") -> List[dict]:
    if user_id not in user_carts:
        user_carts[user_id] = []
    return user_carts[user_id]


@tool
async def get_products() -> str:
    """Get all products"""
    try:
        products = await fake_store_api.get_products()
        return "Here are all available products:\n\n" + "\n".join(
            f"ID: {p['id']} | {p['title']} | ${p['price']} | {p['category']}" 
            for p in products
        )
    except Exception as e:
        return f"Error: {str(e)}"


@tool
async def get_product_details(product_id: int) -> str:
    """Get product details by ID"""
    try:
        p = await fake_store_api.get_product_details(product_id)
        return f"""Product Details:
ID: {p['id']}
Title: {p['title']}
Price: ${p['price']}
Category: {p['category']}
Description: {p['description']}
Rating: {p['rating']['rate']}/5 ({p['rating']['count']} reviews)"""
    except Exception as e:
        return f"Error: {str(e)}"


@tool
async def get_categories() -> str:
    """List product categories"""
    try:
        categories = await fake_store_api.get_categories()
        return "Available categories:\n" + "\n".join(f"- {c}" for c in categories)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
async def get_products_by_category(category: str) -> str:
    """Get products from a category"""
    try:
        products = await fake_store_api.get_products_by_category(category)
        if not products:
            return f"No products in '{category}'"
        
        return f"Products in '{category}':\n\n" + "\n".join(
            f"ID: {p['id']} | {p['title']} | ${p['price']} | {p['rating']['rate']}/5"
            for p in products
        )
    except Exception as e:
        return f"Error: {str(e)}"


@tool
async def search_products(
    query: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> str:
    """Search products with filters"""
    try:
        products = await fake_store_api.get_products_by_category(category) if category else await fake_store_api.get_products()
        results = products
        
        if query:
            q = query.lower()
            results = [p for p in results if q in p['title'].lower() or q in p['description'].lower()]
        
        if min_price:
            results = [p for p in results if p['price'] >= min_price]
        if max_price:
            results = [p for p in results if p['price'] <= max_price]
        
        if not results:
            return "No products found"
        
        filters = []
        if query: filters.append(f"'{query}'")
        if category: filters.append(category)
        if min_price or max_price: filters.append(f"${min_price or 0}-${max_price or '∞'}")
        
        header = f"Found {len(results)} products" + (f" ({', '.join(filters)})" if filters else "")
        return header + ":\n\n" + "\n".join(
            f"ID: {p['id']} | {p['title']} | ${p['price']} | {p['category']} | {p['rating']['rate']}/5"
            for p in results
        )
    except Exception as e:
        return f"Error: {str(e)}"


@tool
async def compare_products(product_ids: List[int]) -> str:
    """Compare products side-by-side"""
    try:
        if len(product_ids) < 2:
            return "Need at least 2 products to compare"
        if len(product_ids) > 5:
            return "Max 5 products"
        
        products = []
        for pid in product_ids:
            try:
                products.append(await fake_store_api.get_product_details(pid))
            except:
                return f"Product {pid} not found"
        
        comp = "## Product Comparison\n\n"
        comp += "**Names:**\n" + "\n".join(f"{i+1}. {p['title']}" for i, p in enumerate(products))
        comp += "\n\n**Prices:**\n" + "\n".join(f"{i+1}. ${p['price']}" for i, p in enumerate(products))
        comp += "\n\n**Ratings:**\n" + "\n".join(f"{i+1}. {p['rating']['rate']}/5" for i, p in enumerate(products))
        
        prices = [p['price'] for p in products]
        ratings = [p['rating']['rate'] for p in products]
        comp += f"\n\n💰 Best Price: #{prices.index(min(prices))+1} (${min(prices)})"
        comp += f"\n⭐ Best Rating: #{ratings.index(max(ratings))+1} ({max(ratings)}/5)"
        
        return comp
    except Exception as e:
        return f"Error: {str(e)}"


@tool
async def add_to_cart(product_id: int, quantity: int = 1) -> str:
    """Add product to cart"""
    try:
        product = await fake_store_api.get_product_details(product_id)
        cart = get_user_cart()
        
        for item in cart:
            if item['product_id'] == product_id:
                item['quantity'] += quantity
                return f"Updated: {product['title']} x{item['quantity']}"
        
        cart.append({
            'product_id': product_id,
            'title': product['title'],
            'price': product['price'],
            'quantity': quantity
        })
        return f"Added: {product['title']} x{quantity} (${product['price']})"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
async def remove_from_cart(product_id: int) -> str:
    """Remove product from cart"""
    try:
        cart = get_user_cart()
        before = len(cart)
        cart[:] = [item for item in cart if item['product_id'] != product_id]
        
        return f"Removed product {product_id}" if len(cart) < before else f"Product {product_id} not in cart"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
async def view_cart() -> str:
    """View cart contents"""
    try:
        cart = get_user_cart()
        if not cart:
            return "Cart is empty"
        
        total = 0
        lines = ["## 🛒 Cart\n"]
        for item in cart:
            subtotal = item['price'] * item['quantity']
            total += subtotal
            lines.append(f"- {item['title']} x{item['quantity']} = ${subtotal:.2f}")
        
        lines.append(f"\n**Total: ${total:.2f}**")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {str(e)}"


tools = [
    get_products,
    get_product_details,
    get_categories,
    get_products_by_category,
    search_products,
    compare_products,
    add_to_cart,
    remove_from_cart,
    view_cart
]
