import os
import requests
from datetime import datetime
from moviepy.editor import ImageSequenceClip
import time

# تنظیمات هارد ۱ ترابایتی محمد عزیز
# یادت باشه ویندوزت که بالا اومد، اگه اسم درایو هاردت چیزی غیر از D بود، این رو عوض کن
BASE_PATH = "D:/my_ai_bot"
GALLERY_PATH = os.path.join(BASE_PATH, "gallery")
VIDEO_PATH = os.path.join(BASE_PATH, "videos")

def setup_folders():
    """ایجاد پوشه‌های لازم روی هارد در صورت عدم وجود"""
    for path in [GALLERY_PATH, VIDEO_PATH]:
        if not os.path.exists(path):
            os.makedirs(path)

def save_and_make_video(image_urls, project_name="ai_project"):
    """
    ۱. دریافت لینک تصاویر از جمینای
    ۲. ذخیره در هارد ۱ ترابایت
    ۳. تبدیل به ویدیو با MoviePy
    """
    setup_folders()
    saved_images = []
    
    # مرحله اول: ذخیره تصاویر در گالری محمد
    print(f"شروع ذخیره‌سازی تصاویر برای پروژه: {project_name}")
    for i, url in enumerate(image_urls):
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{project_name}_{i}_{timestamp}.jpg"
                filepath = os.path.join(GALLERY_PATH, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                saved_images.append(filepath)
                print(f"تصویر {i+1} ذخیره شد: {filepath}")
        except Exception as e:
            print(f"خطا در دانلود تصویر {i}: {e}")

    if not saved_images:
        return None, "محمد جان، هیچ تصویری ذخیره نشد که ویدیو بسازم!"

    # مرحله دوم: تدوین ویدیو (اینجا رم ۸ گیگ و سی‌پی‌یو Xeon میان وسط!)
    try:
        output_video = os.path.join(VIDEO_PATH, f"{project_name}_{int(time.time())}.mp4")
        
        # هر تصویر ۲ ثانیه نمایش داده بشه (fps=0.5)
        clip = ImageSequenceClip(saved_images, fps=0.5) 
        
        # رندر گرفتن با متد libx264 که استاندارد اینستاگرامه
        clip.write_videofile(output_video, fps=24, codec="libx264", audio=False)
        
        return output_video, get_tutor_lesson()
    except Exception as e:
        return None, f"خطا در ساخت ویدیو: {e}"

def get_tutor_lesson():
    """پیام آموزشی مخصوص محمد برای یادگیری پایتون"""
    lesson = (
        "🎓 **درس امروز معلم خصوصی پایتون:**\n\n"
        "محمد جان، تبریک می‌گم! تو الان از کتابخانه `moviepy` استفاده کردی.\n"
        "۱. **اتوماسیون:** ما به جای اینکه دستی ویدیو بسازیم، با کد به سیستم گفتیم عکس‌ها رو رندر کنه.\n"
        "۲. **مدیریت فایل:** با استفاده از کتابخانه `os` یاد گرفتی چطور پوشه‌ها رو مدیریت کنی و دیتا رو روی هارد ۱ ترابایتی‌ت دسته‌بندی کنی.\n"
        "۳. **پردازش سنگین:** ساخت ویدیو بیشترین فشار رو به رم ۸ گیگابایتی‌ت میاره، پس همیشه فن سی‌پی‌یو رو چک کن!"
    )
    return lesson
