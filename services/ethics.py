def is_ethical_request(text):
    # لیست کلمات ممنوعه یا الگوهای غیرقانونی
    forbidden_words = ["هک", "ساخت بمب", "مواد مخدر", "hack", "crack"]
    for word in forbidden_words:
        if word in text.lower():
            return False
    return True

def get_ethics_rejection_message(lang="fa"):
    messages = {
        "fa": "⚠️ متأسفم، من نمی‌توانم در مورد درخواست‌های غیرقانونی یا غیراخلاقی کمک کنم.",
        "en": "⚠️ I'm sorry, I cannot assist with illegal or unethical requests.",
        "ar": "⚠️ عذراً، لا أستطيع المساعدة في الطلبات غیر القانونية."
    }
    return messages.get(lang, messages["fa"])
