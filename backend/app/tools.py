from langchain_core.tools import tool
from app.api_client import fake_store_api
from typing import Optional, List
from contextvars import ContextVar
from sqlalchemy.orm import Session
from app.vector_store import get_vector_store

# Context variable to pass db session to tools
db_session: ContextVar[Optional[Session]] = ContextVar('db_session', default=None)


def get_user_cart_from_db(user_id: str = "default") -> List[dict]:
    """Get cart items from database"""
    from app.database import CartItem
    db = db_session.get()
    if not db:
        return []
    
    cart_items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    return [
        {
            'product_id': item.product_id,
            'title': item.title,
            'price': float(item.price),
            'quantity': item.quantity
        }
        for item in cart_items
    ]


def normalize_category(category: str) -> str:
    """Normalize category names to match API expectations"""
    category_lower = category.lower().strip()
    
    # Category mappings
    category_map = {
        'men': "men's clothing",
        "men's": "men's clothing",
        'mens': "men's clothing",
        "men's clothing": "men's clothing",
        "mens clothing": "men's clothing",
        'women': "women's clothing",
        "women's": "women's clothing",
        'womens': "women's clothing",
        "women's clothing": "women's clothing",
        "womens clothing": "women's clothing",
        'electronics': 'electronics',
        'electronic': 'electronics',
        'tech': 'electronics',
        'jewelery': 'jewelery',
        'jewelry': 'jewelery',
        'jewellery': 'jewelery'
    }
    
    return category_map.get(category_lower, category)


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
    """Get products from a category. Supports: electronics, jewelery, men's clothing, women's clothing, or variations like 'men', 'women'"""
    try:
        normalized_category = normalize_category(category)
        products = await fake_store_api.get_products_by_category(normalized_category)
        if not products:
            return f"No products found in '{category}'. Available categories: electronics, jewelery, men's clothing, women's clothing"
        
        return f"Products in '{normalized_category}':\n\n" + "\n".join(
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
    """Search products with filters. Uses semantic search when query is provided for better understanding of user intent."""
    try:
        normalized_category = normalize_category(category) if category else None
        products = await fake_store_api.get_products_by_category(normalized_category) if normalized_category else await fake_store_api.get_products()
        results = products
        
        # Use semantic search if query is provided and vector store is available
        if query:
            vector_store = get_vector_store()
            if vector_store.index is not None:
                # Semantic search finds products by meaning, not just keywords
                results = vector_store.search(query, top_k=20)
                # Apply category filter if specified
                if normalized_category:
                    results = [p for p in results if p.get('category') == normalized_category]
            else:
                # Fallback to keyword search
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
        from app.database import CartItem
        product = await fake_store_api.get_product_details(product_id)
        db = db_session.get()
        
        if not db:
            return "Error: Database not available"
        
        # Check if item already exists in cart
        existing_item = db.query(CartItem).filter(
            CartItem.user_id == "default",
            CartItem.product_id == product_id
        ).first()
        
        if existing_item:
            existing_item.quantity += quantity
            db.commit()
            return f"Updated: {product['title']} x{existing_item.quantity}"
        
        # Add new item to cart
        cart_item = CartItem(
            user_id="default",
            product_id=product_id,
            title=product['title'],
            price=str(product['price']),
            quantity=quantity
        )
        db.add(cart_item)
        db.commit()
        return f"Added: {product['title']} x{quantity} (${product['price']})"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
async def remove_from_cart(product_id: int) -> str:
    """Remove product from cart"""
    try:
        from app.database import CartItem
        db = db_session.get()
        
        if not db:
            return "Error: Database not available"
        
        cart_item = db.query(CartItem).filter(
            CartItem.user_id == "default",
            CartItem.product_id == product_id
        ).first()
        
        if cart_item:
            db.delete(cart_item)
            db.commit()
            return f"Removed product {product_id} from cart"
        
        return f"Product {product_id} not in cart"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
async def view_cart() -> str:
    """View cart contents"""
    try:
        from app.database import CartItem
        db = db_session.get()
        
        if not db:
            return "Error: Database session not available"
        
        db.expire_all()
        
        cart_items = db.query(CartItem).filter(CartItem.user_id == "default").all()
        
        if not cart_items:
            return "Cart is empty"
        
        total = 0
        lines = ["## 🛒 Cart\n"]
        for item in cart_items:
            subtotal = float(item.price) * item.quantity
            total += subtotal
            lines.append(f"- {item.title} x{item.quantity} = ${subtotal:.2f}")
        
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
