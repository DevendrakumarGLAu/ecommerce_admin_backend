"""Import all models here so Alembic's autogenerate can discover them via Base.metadata."""

from app.models.cart import Cart, CartItem
from app.models.category import Category
from app.models.password_reset_otp import PasswordResetOTP
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_marketplace_link import ProductMarketplaceLink
from app.models.product_video import ProductVideo
from app.models.settings import Settings
from app.models.user import User
from app.models.wishlist import Wishlist

__all__ = [
    "User",
    "Category",
    "Product",
    "ProductImage",
    "ProductMarketplaceLink",
    "ProductVideo",
    "PasswordResetOTP",
    "Cart",
    "CartItem",
    "Wishlist",
    "Settings",
]
