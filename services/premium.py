def check_access_level(user_id: int) -> str:
    """
    بررسی سطح دسترسی کاربر.
    در نسخهٔ پایه، همه کاربران 'free' هستند.
    در نسخهٔ کامل، این تابع از Appwrite یا دیتابیس خوانده می‌شود.
    """
    return "free"

def get_premium_features(level: str) -> str:
    return "در حال توسعه..."
