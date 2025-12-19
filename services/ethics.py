import re

def is_ethical_request(text: str) -> bool:
    """
    بررسی می‌کند که آیا متن درخواستی از کاربر حاوی محتوای غیرقانونی، آسیب‌زننده یا غیراخلاقی است.
    """
    if not text or not isinstance(text, str):
        return False

    text = text.lower().strip()

    unethical_patterns = [
        r"\b(hack|phishing|scam|fake|trick|دزد|سرقت|کلاه|فیش|کلاهبردار|دروغ|فریب|فروش ساقط)\b",
        r"\b(doxx?|swat|attack|threat|harass|آزار|تهدید|آسیب|خشونت|جنگ|کشتن|ترور)\b",
        r"\b(bypass|crack|exploit|illegal|غیرقانونی|فیلترشکن|دور زدن|خرابکاری|هک|ورود غیرمجاز|بدافزار)\b",
        r"\b(drug|weapon|bomb|قمار|مخدر|سلاح|انفجار|تروریست|شبح|کریپتو اسکم)\b",
        r"(union\s+select|select\s+\*|drop\s+table|--|<script|javascript:|onload\s*=|\.exe|\.bat)",
    ]

    return not any(re.search(pattern, text, re.IGNORECASE) for pattern in unethical_patterns)


def get_ethics_rejection_message(lang: str = "fa") -> str:
    """
    پیام استاندارد برای رد درخواست‌های غیراخلاقی — به چند زبان.
    """
    messages = {
        "fa": (
            "⚠️ **درخواست شما پردازش نمی‌شود.**\n"
            "من یک ربات هوشمند هستم که **صرفاً در خدمت آگاهی، یادگیری و عدالت** است.\n"
            "هیچ‌گاه در فعالیت‌های غیرقانونی، کلاهبرداری، آسیب‌رسانی به دیگران یا دور زدن امنیت کمک نمی‌کنم.\n"
            "اگر سؤالی دربارهٔ آموزش، تحلیل بازار، حقوق یا نویسندگی داری، خوشحال می‌شم کمک کنم."
        ),
        "en": (
            "⚠️ **Your request cannot be processed.**\n"
            "I am an AI assistant dedicated **only to knowledge, justice, and learning**.\n"
            "I do not assist with fraud, harm, illegal acts, or bypassing security.\n"
            "If you have questions about education, market analysis, legal writing, or research, I’d be glad to help."
        ),
        "ar": (
            "⚠️ **لا يمكن معالجة طلبك.**\n"
            "أنا مساعد ذكي مخصص **للمعرفة والعدالة والتعلم فقط**.\n"
            "لا أساعد في الاحتيال أو الإيذاء أو الأنشطة غير القانونية أو تجاوز الأمان.\n"
            "إذا كانت لديك أسئلة حول التعليم أو تحليل السوق أو الكتابة القانونية أو البحث، فسأكون سعيدًا بمساعدتك."
        )
    }
    return messages.get(lang, messages["fa"])
