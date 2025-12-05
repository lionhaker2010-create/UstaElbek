# admin.py - TO'LIQ YANGILASH

from aiogram import Bot, F
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    Message, CallbackQuery,
    PhotoSize, Video, Document,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode

from database import db
import asyncio
import logging
from datetime import datetime

# ✅ TO'G'RI: AdminStates class'ini bu yerda yaratamiz (FAQAT BIR MARTTA)
class AdminStates(StatesGroup):
    # Kontent qo'shish
    adding_content = State()
    waiting_for_content = State()
    waiting_for_caption = State()
    
    # Xabar yuborish
    sending_message = State()
    waiting_broadcast_text = State()
    waiting_broadcast_photo = State()
    waiting_broadcast_video = State()
    waiting_broadcast_document = State()
    
    # Bloklash
    blocking_user = State()
    unblocking_user = State()
    
    # Kontent o'chirish
    deleting_content = State()
    waiting_content_id = State()

# ✅ Bot va admin ID uchun global o'zgaruvchilar
bot = None
ADMIN_ID = None

def set_bot_and_admin(bot_instance, admin_id):
    """Bot va admin ID ni sozlash"""
    global bot, ADMIN_ID
    bot = bot_instance
    ADMIN_ID = admin_id

# Logging
logger = logging.getLogger(__name__)

# Admin panel klaviaturasi
def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Foydalanuvchilar Ma'lumotlari"), KeyboardButton(text="📨 Xabar Yuborish")],
            [KeyboardButton(text="➕ Kontent Qo'shish"), KeyboardButton(text="🗑️ Kontent O'chirish")],
            [KeyboardButton(text="🚫 Bloklash"), KeyboardButton(text="✅ Blokdan Ochish")],
            [KeyboardButton(text="📋 Kontentlar Ro'yxati"), KeyboardButton(text="📍 Joylashuvni Ko'rish")],
            [KeyboardButton(text="🔙 Asosiy Menyuga Qaytish")]
        ],
        resize_keyboard=True,
        persistent=True
    )

def get_content_categories_keyboard(action: str = "add"):
    """Kontent kategoriyalari klaviaturasi"""
    if action == "add":
        text = "📂 Kontent qo'shish uchun kategoriyani tanlang:"
        keyboard = [
            [KeyboardButton(text="🛠️ Klassik Tamirlash"), KeyboardButton(text="🎨 Lepka Yopishtirish")],
            [KeyboardButton(text="🏠 Gipsi Carton Fason"), KeyboardButton(text="💻 HiTech Tamirlash")],
            [KeyboardButton(text="🔨 To'liq Tamirlash"), KeyboardButton(text="📹 Video Joylash")],
            [KeyboardButton(text="🔙 Orqaga")]
        ]
    else:  # delete
        text = "🗑️ O'chirish uchun kategoriyani tanlang:"
        keyboard = [
            [KeyboardButton(text="🛠️ Klassik Tamirlash"), KeyboardButton(text="🎨 Lepka Yopishtirish")],
            [KeyboardButton(text="🏠 Gipsi Carton Fason"), KeyboardButton(text="💻 HiTech Tamirlash")],
            [KeyboardButton(text="🔨 To'liq Tamirlash"), KeyboardButton(text="📹 Video Joylash")],
            [KeyboardButton(text="🔙 Orqaga")]
        ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True), text

def get_content_type_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🖼️ Rasm"), KeyboardButton(text="📹 Video")],
            [KeyboardButton(text="📄 Dokument"), KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

def get_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

def get_protection_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔒 Yuqori Himoya"), KeyboardButton(text="🛡️ O'rta Himoya")],
            [KeyboardButton(text="⚠️ Past Himoya"), KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

async def set_protection_level(message: Message, state: FSMContext):
    """Himoya darajasini sozlash"""
    if message.from_user.id != ADMIN_ID:
        return
    
    protection_map = {
        "🔒 Yuqori Himoya": 3,
        "🛡️ O'rta Himoya": 2,
        "⚠️ Past Himoya": 1
    }
    
    if message.text in protection_map:
        level = protection_map[message.text]
        await state.update_data(protection_level=level)
        await message.answer(f"✅ Himoya darajasi {level} ga o'rnatildi")    

# Kontent qo'shishni boshlash
async def start_adding_content(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    # FSM holatini aniq o'rnatish
    await state.set_state(AdminStates.adding_content)
    
    keyboard, text = get_content_categories_keyboard("add")
    
    await message.answer(text, reply_markup=keyboard)

# Kategoriyani tanlash
async def process_content_category(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    # Kategoriya mapping
    categories_map = {
        # Admin panel tugmalari
        "🛠️ Klassik Tamirlash": "classic",
        "🎨 Lepka Yopishtirish": "glue", 
        "🏠 Gipsi Carton Fason": "gypsum",
        "💻 HiTech Tamirlash": "hitech",
        "🔨 To'liq Tamirlash": "full",
        "📹 Video Joylash": "video",
        
        # Asosiy menyu tugmalari (O'zbek)
        "Klassik Tamirlash": "classic",
        "Lepka Yopishtirish": "glue",
        "Gipsi Carton Fason": "gypsum", 
        "HiTech Tamirlash": "hitech",
        "To'liq Tamirlash": "full",
        "Video Ishlar": "video",
        
        # Asosiy menyu tugmalari (Rus)
        "Классический Ремонт": "classic",
        "Поклейка Обоев": "glue",
        "Гипсокартон Фасон": "gypsum",
        "HiTech Ремонт": "hitech",
        "Полный Ремонт": "full",
        "Видео Работы": "video"
    }
    
    current_state = await state.get_state()
    
    # AGAR ADMIN PANEL HOLATIDA BO'LSA (adding_content)
    if current_state == AdminStates.adding_content.state:
        if message.text in categories_map:
            # Kategoriyani saqlash
            category_code = categories_map[message.text]
            await state.update_data(category=category_code)
            await state.set_state(AdminStates.waiting_for_content)
            
            await message.answer("📄 Kontent turini tanlang:", reply_markup=get_content_type_keyboard())
            return
        elif message.text == "🔙 Orqaga":
            await state.clear()
            await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
            return
        else:
            if "To'liq Tamirlash" in message.text or "Полный Ремонт" in message.text:
                await state.update_data(category="full")
                await state.set_state(AdminStates.waiting_for_content)
                await message.answer("📄 Kontent turini tanlang:", reply_markup=get_content_type_keyboard())
                return
    
    await message.answer("❌ Kategoriya tanlashda xatolik!")

# Kontent turini tanlash
async def process_content_type(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    content_types = {
        "🖼️ Rasm": "photo",
        "📹 Video": "video",
        "📄 Dokument": "document"
    }
    
    if message.text not in content_types:
        if message.text == "🔙 Orqaga":
            keyboard, text = get_content_categories_keyboard("add")
            await message.answer(text, reply_markup=keyboard)
            await state.set_state(AdminStates.adding_content)
            return
        await message.answer("❌ Iltimos, ro'yxatdagi turlardan birini tanlang!")
        return
    
    await state.update_data(content_type=content_types[message.text])
    
    await message.answer("📤 Iltimos, faylni yuboring (rasm, video yoki dokument):", reply_markup=get_back_keyboard())
    await state.set_state(AdminStates.waiting_for_caption)

async def process_content_file(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    # Agar foydalanuvchi orqaga qaytishni xohlasa
    if message.text and message.text == "🔙 Orqaga":
        await message.answer("📄 Kontent turini tanlang:", reply_markup=get_content_type_keyboard())
        await state.set_state(AdminStates.waiting_for_content)
        return
    
    data = await state.get_data()
    category = data.get('category')
    content_type = data.get('content_type')
    
    file_id = None
    caption = message.caption or ""
    
    # Fayl ID sini olish
    if content_type == "photo" and message.photo:
        file_id = message.photo[-1].file_id
    elif content_type == "video" and message.video:
        file_id = message.video.file_id
    elif content_type == "document" and message.document:
        file_id = message.document.file_id
    else:
        await message.answer("❌ Iltimos, to'g'ri formatdagi faylni yuboring!", reply_markup=get_back_keyboard())
        return
    
    # Faqat admin yozgan caption saqlanadi
    protected_caption = caption
    
    # Bazaga saqlash
    try:
        content_id = db.add_content(category, content_type, file_id, protected_caption)
        
        # Kategoriya nomi
        category_names = {
            "classic": "Klassik Tamirlash",
            "glue": "Lepka Yopishtirish",
            "gypsum": "Gipsi Carton Fason",
            "hitech": "HiTech Tamirlash",
            "full": "To'liq Tamirlash",
            "video": "Video Joylash"
        }
        
        category_name = category_names.get(category, category)
        
        success_message = (
            f"✅ Kontent muvaffaqiyatli qo'shildi!\n\n"
            f"📁 Kategoriya: {category_name}\n"
            f"📄 Tur: {content_type}\n"
            f"🆔 ID: {content_id}"
        )
        
        if caption:
            success_message += f"\n📝 Izoh: {caption[:50] + '...' if len(caption) > 50 else caption}"
        
        await message.answer(success_message)
        
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
    
    # Admin panelga qaytish
    await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
    await state.clear()

# Foydalanuvchilar ma'lumotlari
async def show_users_info(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    users = db.get_all_users()
    if not users:
        await message.answer("📭 Hech qanday foydalanuvchi topilmadi.")
        return
    
    active_users = db.get_active_users()
    blocked_users = db.get_blocked_users()
    
    text = "📊 FOYDALANUVCHILAR STATISTIKASI\n\n"
    text += f"👥 Jami foydalanuvchilar: {len(users)}\n"
    text += f"✅ Faol foydalanuvchilar: {len(active_users)}\n"
    text += f"🚫 Bloklanganlar: {len(blocked_users)}\n"
    text += "------------------------------\n\n"
    text += "📋 So'ngi 10 ta foydalanuvchi:\n\n"
    
    for user in users[-10:]:
        status = "🚫 Bloklangan" if user[5] == 1 else "✅ Faol"
        reg_date = user[4].split()[0] if isinstance(user[4], str) else str(user[4])[:10]
        text += f"👤 ID: {user[0]}\nIsm: {user[1]}\nTel: {user[2]}\nTil: {user[3]}\nRo'yxatdan: {reg_date}\nHolat: {status}\n--------------------\n"
    
    await message.answer(text, parse_mode=ParseMode.HTML)

# Xabar yuborishni boshlash
async def start_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    # Yangi klaviatura
    broadcast_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Matnli reklama")],
            [KeyboardButton(text="🖼️ Rasmli reklama")],
            [KeyboardButton(text="📹 Videoli reklama")],
            [KeyboardButton(text="📄 Dokument reklama")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "📤 <b>Reklama yuborish:</b>\n\n"
        "Quyidagi formatlardan birini tanlang:\n"
        "• 📝 <b>Matn</b> - oddiy matnli reklama\n"
        "• 🖼️ <b>Rasm</b> - rasm + matnli reklama\n"
        "• 📹 <b>Video</b> - video + matnli reklama\n"
        "• 📄 <b>Dokument</b> - fayl + matnli reklama",
        reply_markup=broadcast_keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(AdminStates.sending_message)

# Xabarning turini tanlash
async def process_broadcast_type(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "📝 Matnli reklama":
        await message.answer(
            "✍️ <b>Matnli reklama yuborish:</b>\n\n"
            "Iltimos, reklama matnini kiriting (HTML formatida bo'lishi mumkin):\n\n"
            "<i>Namuna:</i>\n"
            "<code>🎉 Yangi chegirma!\n\n"
            "🏠 Tamirlash xizmatlari uchun 20% chegirma!\n"
            "📞 +998 95 902-32-32</code>",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(AdminStates.waiting_broadcast_text)
        
    elif message.text == "🖼️ Rasmli reklama":
        await message.answer(
            "🖼️ <b>Rasmli reklama yuborish:</b>\n\n"
            "Iltimos, rasmni yuboring (rasm caption'ida reklama matni bo'lishi mumkin):",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(AdminStates.waiting_broadcast_photo)
        
    elif message.text == "📹 Videoli reklama":
        await message.answer(
            "📹 <b>Videoli reklama yuborish:</b>\n\n"
            "Iltimos, videoni yuboring (video caption'ida reklama matni bo'lishi mumkin):",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(AdminStates.waiting_broadcast_video)
        
    elif message.text == "📄 Dokument reklama":
        await message.answer(
            "📄 <b>Dokument reklama yuborish:</b>\n\n"
            "Iltimos, dokumentni yuboring (dokument caption'ida reklama matni bo'lishi mumkin):",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(AdminStates.waiting_broadcast_document)
        
    elif message.text == "🔙 Orqaga":
        await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        await state.clear()

# Matnli reklama
async def process_broadcast_text(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 Orqaga":
        await start_broadcast(message, state)
        return
    
    # Reklama matnini saqlash
    await state.update_data(broadcast_text=message.text)
    
    # Tasdiqlash
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, yuborish", callback_data="confirm_broadcast:text"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")
        ]
    ])
    
    await message.answer(
        f"📤 <b>Reklama tayyor:</b>\n\n"
        f"{message.text}\n\n"
        f"✅ <b>Barcha foydalanuvchilarga yuborilsinmi?</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# Rasmli reklama
async def process_broadcast_photo(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text and message.text == "🔙 Orqaga":
        await start_broadcast(message, state)
        return
    
    if not message.photo:
        await message.answer("❌ Iltimos, rasm yuboring!", reply_markup=get_back_keyboard())
        return
    
    # Rasm va caption'ni saqlash
    photo_id = message.photo[-1].file_id
    caption = message.caption or ""
    
    await state.update_data(
        broadcast_type="photo",
        broadcast_file_id=photo_id,
        broadcast_caption=caption
    )
    
    # Tasdiqlash
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, yuborish", callback_data="confirm_broadcast:photo"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")
        ]
    ])
    
    preview_text = f"📸 <b>Rasmli reklama tayyor:</b>\n\n{caption}" if caption else "📸 <b>Rasmli reklama tayyor</b>"
    
    await message.answer_photo(
        photo=photo_id,
        caption=f"{preview_text}\n\n✅ <b>Barcha foydalanuvchilarga yuborilsinmi?</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# Bloklashni boshlash
async def start_blocking_user(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.set_state(AdminStates.blocking_user)
    
    await message.answer(
        "🚫 Bloklash uchun foydalanuvchi ID sini yuboring:",
        reply_markup=get_back_keyboard()
    )

# admin.py faylida process_block_user funksiyasini shunday tuzating:

async def process_block_user(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 Orqaga":
        await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        await state.clear()
        return
    
    try:
        user_id = int(message.text)
        user_data = db.get_user(user_id)
        
        if not user_data:
            await message.answer(f"❌ ID {user_id} bilan foydalanuvchi topilmadi!")
            return
        
        # Foydalanuvchini bloklash
        db.block_user(user_id)
        
        # ✅ YANGI: Bloklanganligi haqida foydalanuvchiga OGOHLANTIRISH XABARI yuborish
        try:
            lang = user_data[3]
            
            # Til bo'yicha xabar matnlari
            block_messages = {
                "uz": """🚫 <b>OGOHLANTIRISH!</b>

❌ <b>Sizning hisobingiz bloklandi!</b>

Botdan foydalana olmaysiz.

⚖️ <b>Bloklash sabablari:</b>
• Bot qoidalarini buzganingiz uchun
• Kontentlarni yuklab olganingiz yoki ko'chirganingiz uchun
• Noto'g'ri xatti-harakatlar uchun

📞 <b>Shikoyat yoki izoh uchun:</b>
+998 95 902-32-32

⚠️ <b>Eslatma:</b>
Agar sizda savollar bo'lsa yoki xatolik deb o'ylasangiz, yuqoridagi raqamga qo'ng'iroq qiling.

⏰ <b>Bloklash muddati:</b>
Cheklanmagan (admin tomonidan olib tashlanmaguncha)

📝 <b>Qayta ochilish uchun:</b>
• Admin bilan bog'laning
• Sababni tushuntiring
• Kafolat bering

<code>© Usta Elbek. Barcha huquqlar himoyalangan.</code>""",
                
                "ru": """🚫 <b>ПРЕДУПРЕЖДЕНИЕ!</b>

❌ <b>Ваш аккаунт заблокирован!</b>

Вы не можете использовать бота.

⚖️ <b>Причины блокировки:</b>
• За нарушение правил бота
• За скачивание или копирование контента
• За неподобающее поведение

📞 <b>Для жалоб или комментариев:</b>
+998 95 902-32-32

⚠️ <b>Примечание:</b>
Если у вас есть вопросы или вы считаете это ошибкой, позвоните по указанному номеру.

⏰ <b>Срок блокировки:</b>
Неограниченный (пока не снят администратором)

📝 <b>Для разблокировки:</b>
• Свяжитесь с администратором
• Объясните причину
• Дайте гарантии

<code>© Usta Elbek. Все права защищены.</code>"""
            }
            
            # Foydalanuvchiga xabar yuborish
            await bot.send_message(
                user_id, 
                block_messages[lang], 
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Failed to send block message: {e}")
        
        # ✅ TO'G'RI: Admin uchun muvaffaqiyatli xabar (format usuli)
        success_message = (
            "✅ <b>Foydalanuvchi muvaffaqiyatli bloklandi!</b>\n\n"
            "👤 <b>Ism:</b> {}\n"
            "🆔 <b>ID:</b> {}\n"
            "📞 <b>Telefon:</b> {}\n"
            "🌐 <b>Til:</b> {}\n\n"
            "📨 <b>Foydalanuvchiga ogohlantirish xabari yuborildi!</b>"
        ).format(
            user_data[1],
            user_id,
            user_data[2],
            "🇺🇿 O'zbek" if user_data[3] == 'uz' else "🇷🇺 Русский"  # ✅ Format ichida apostrof muammosiz
        )
        
        await message.answer(success_message, parse_mode="HTML")
        
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri ID kiriting (faqat raqam)!")
        return
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
    
    await state.clear()
    await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())

# Blokdan ochishni boshlash
async def start_unblocking_user(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.set_state(AdminStates.unblocking_user)
    
    blocked_users = db.get_blocked_users()
    
    if not blocked_users:
        await message.answer("🚫 Hozirda hech qanday bloklangan foydalanuvchi yo'q.")
        return
    
    text = "🔒 Bloklangan foydalanuvchilar:\n\n"
    for user in blocked_users:
        text += f"👤 ID: {user[0]} | Ism: {user[1]} | Tel: {user[2]}\n"
    
    text += "\n✅ Blokdan ochish uchun foydalanuvchi ID sini yuboring:"
    
    await message.answer(text, reply_markup=get_back_keyboard())

async def process_unblock_user(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 Orqaga":
        await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        await state.clear()
        return
    
    try:
        user_id = int(message.text)
        user_data = db.get_user(user_id)
        
        if not user_data:
            await message.answer(f"❌ ID {user_id} bilan foydalanuvchi topilmadi!")
            return
        
        # Foydalanuvchini blokdan ochish
        db.unblock_user(user_id)
        
        # ✅ Blokdan ochilganligi haqida foydalanuvchiga CHIROYLI XABAR yuborish
        try:
            lang = user_data[3]
            
            # Til bo'yicha xabar matnlari
            unblock_messages = {
                "uz": """🎉 <b>Tabriklaymiz!</b>

✅ <b>Sizning hisobingiz blokdan olindi!</b>

Siz endi Usta Elbek botidan to'liq foydalana olasiz.

⚠️ <b>OGOHLANTIRISH:</b>
• Bot qoidalariga qat'iy rioya qiling
• Kontentlarni yuklab olish yoki ko'chirish taqiqlanadi
• Qonuniy huquqlarni buzish javobgarlikni keltirib chiqaradi

📞 <b>Yordam uchun:</b>
+998 95 902-32-32

🏠 <b>Xizmatlar:</b>
• Klassik tamirlash
• Lepka yopishtirish
• Gipsi carton fason
• HiTech tamirlash
• To'liq tamirlash

🎨 <b>Bizning maqsadimiz:</b>
Uyingizni chiroyli va zamonaviy qilish!

📍 <b>Manzil:</b> Toshkent

⏰ <b>Ish vaqtlari:</b>
Dushanba-Yakshanba: 9:00 - 18:00

💖 <b>Xursand mijoz - bizning maqsadimiz!</b>

<code>© Usta Elbek. Barcha huquqlar himoyalangan.</code>""",
                
                "ru": """🎉 <b>Поздравляем!</b>

✅ <b>Ваш аккаунт разблокирован!</b>

Теперь вы можете полноценно пользоваться ботом Мастера Элбека.

⚠️ <b>ПРЕДУПРЕЖДЕНИЕ:</b>
• Строго соблюдайте правила бота
• Запрещено скачивать или копировать контент
• Нарушение законных прав влечет ответственность

📞 <b>Для помощи:</b>
+998 95 902-32-32

🏠 <b>Услуги:</b>
• Классический ремонт
• Поклейка обоев
• Гипсокартон фасон
• HiTech ремонт
• Полный ремонт

🎨 <b>Наша цель:</b>
Сделать ваш дом красивым и современным!

📍 <b>Адрес:</b> Ташкент

⏰ <b>Время работы:</b>
Понедельник-Воскресенье: 9:00 - 18:00

💖 <b>Довольный клиент - наша цель!</b>

<code>© Usta Elbek. Все права защищены.</code>"""
            }
            
            # Foydalanuvchiga xabar yuborish
            await bot.send_message(
                user_id, 
                unblock_messages[lang], 
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Failed to send unblock message: {e}")
        
        # Admin uchun muvaffaqiyatli xabar (format() usuli)
        success_message = (
            "✅ <b>Foydalanuvchi muvaffaqiyatli blokdan olindi!</b>\n\n"
            "👤 <b>Ism:</b> {}\n"
            "🆔 <b>ID:</b> {}\n"
            "📞 <b>Telefon:</b> {}\n"
            "🌐 <b>Til:</b> {}\n\n"
            "📨 <b>Foydalanuvchiga xabar yuborildi!</b>"
        ).format(
            user_data[1],
            user_id,
            user_data[2],
            "🇺🇿 O'zbek" if user_data[3] == 'uz' else "🇷🇺 Русский"
        )
        
        await message.answer(success_message, parse_mode="HTML")
        
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri ID kiriting (faqat raqam)!")
        return
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
    
    await state.clear()
    await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())

# Kontentlar ro'yxati
async def show_contents_list(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    contents = db.get_all_contents()
    
    if not contents:
        await message.answer("📭 Hech qanday kontent topilmadi.")
        return
    
    # Kategoriya nomlari
    category_names = {
        "classic": "🛠️ Klassik Tamirlash",
        "glue": "🎨 Lepka Yopishtirish",
        "gypsum": "🏠 Gipsi Carton Fason",
        "hitech": "💻 HiTech Tamirlash",
        "full": "🔨 To'liq Tamirlash",
        "video": "📹 Video Joylash"
    }
    
    # Tur nomlari
    type_names = {
        "photo": "🖼️ Rasm",
        "video": "📹 Video",
        "document": "📄 Dokument"
    }
    
    text = "📋 Barcha kontentlar:\n\n"
    
    for content in contents[:20]:
        category = category_names.get(content[1], content[1])
        content_type = type_names.get(content[2], content[2])
        date = content[5].split()[0] if isinstance(content[5], str) else str(content[5])[:10]
        
        text += f"🆔 ID: {content[0]}\n"
        text += f"📁 {category}\n"
        text += f"📄 {content_type}\n"
        text += f"📅 {date}\n"
        if content[4]:
            caption_preview = content[4][:30] + "..." if len(content[4]) > 30 else content[4]
            text += f"📝 {caption_preview}\n"
        text += "------------------------------\n"
    
    if len(contents) > 20:
        text += f"\n📊 Jami: {len(contents)} ta kontent (faqat 20 tasi ko'rsatilgan)"
    
    await message.answer(text)

# Kontent o'chirishni boshlash
async def start_deleting_content(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    keyboard, text = get_content_categories_keyboard("delete")
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(AdminStates.deleting_content)

# Kategoriya bo'yicha o'chirish
async def process_delete_category(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    # Kategoriya mapping
    categories_map = {
        "🛠️ Klassik Tamirlash": "classic",
        "🎨 Lepka Yopishtirish": "glue", 
        "🏠 Gipsi Carton Fason": "gypsum",
        "💻 HiTech Tamirlash": "hitech",
        "🔨 To'liq Tamirlash": "full",
        "📹 Video Joylash": "video"
    }
    
    if message.text not in categories_map:
        if message.text == "🔙 Orqaga":
            await state.clear()
            await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
            return
        await message.answer("❌ Iltimos, ro'yxatdagi kategoriyalardan birini tanlang!")
        return
    
    category = categories_map[message.text]
    contents = db.get_contents_by_category(category)
    
    if not contents:
        await message.answer(f"❌ '{message.text}' kategoriyasida hech qanday kontent topilmadi.")
        await state.clear()
        await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        return
    
    # Kontentlarni INLINE KLAVIATURA bilan ko'rsatish
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    text = f"🗑️ <b>'{message.text}' kategoriyasidagi kontentlar:</b>\n\n"
    
    for content in contents:
        content_id = content[0]
        content_type = "🖼️" if content[2] == 'photo' else "📹" if content[2] == 'video' else "📄"
        date = content[5].split()[0] if isinstance(content[5], str) else str(content[5])[:10]
        
        text += f"<b>🆔 {content_id}</b> | {content_type} | 📅 {date}\n"
        
        if content[4]:
            caption_preview = content[4][:30] + "..." if len(content[4]) > 30 else content[4]
            text += f"📝 {caption_preview}\n"
        
        text += "─" * 30 + "\n"
    
    # INLINE KLAVIATURA YARATISH
    keyboard = []
    
    # Har bir kontent uchun o'chirish tugmasi
    for content in contents:
        content_id = content[0]
        content_type = "🖼️" if content[2] == 'photo' else "📹" if content[2] == 'video' else "📄"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ O'chirish #{content_id} ({content_type})",
                callback_data=f"delete_content:{content_id}"
            )
        ])
    
    # Barchasini bir vaqtda o'chirish tugmasi
    keyboard.append([
        InlineKeyboardButton(
            text="🗑️ BARCHASINI O'CHIRISH",
            callback_data=f"delete_all:{category}"
        )
    ])
    
    # Orqaga tugmasi
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data="delete_back"
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await state.clear()

# Joylashuvlarni ko'rsatish
async def show_latest_locations(message: Message):
    """Eng so'nggi joylashuvlarni ko'rsatish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    locations = db.get_latest_locations()
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    if not locations:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Yangilash",
                    callback_data="refresh_locations_admin"
                )
            ]
        ])
        
        await message.answer(
            "📍 <b>Hech qanday joylashuv yo'q.</b>\n\n"
            "Foydalanuvchilar joylashuv yuborganda, bu yerda ko'rinadi.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    # Eng so'nggi joylashuvni ko'rsatish
    latest_location = locations[0]
    location_id = latest_location[0]
    user_name = latest_location[2]
    phone = latest_location[3]
    status = latest_location[6]
    sent_time = latest_location[7].split()[1][:5] if isinstance(latest_location[7], str) else str(latest_location[7])[11:16]
    
    # Status ranglari
    status_emoji = "🟡" if status == 'pending' else "🟢" if status == 'accepted' else "🔴"
    
    text = f"""📍 <b>ENG SO'NGI JOYLASHUV:</b>

{status_emoji} <b>Holat:</b> {status}
🆔 <b>ID:</b> {location_id}
👤 <b>Foydalanuvchi:</b> {user_name}
📞 <b>Telefon:</b> {phone}
⏰ <b>Vaqt:</b> {sent_time}

✅ <i>Joylashuvni ko'rib, tasdiqlang yoki rad eting</i>"""
    
    # Inline klaviatura
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📍 Joylashuvni ko'rish",
                callback_data=f"view_location:{location_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Tasdiqlash",
                callback_data=f"accept_location:{location_id}"
            ),
            InlineKeyboardButton(
                text="❌ Rad etish",
                callback_data=f"reject_location:{location_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Barcha joylashuvlar",
                callback_data="view_all_locations_admin"
            ),
            InlineKeyboardButton(
                text="🔄 Yangilash",
                callback_data="refresh_locations_admin"
            )
        ]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# Barcha joylashuvlarni ko'rsatish
async def show_all_locations_admin(message: Message):
    """Barcha joylashuvlarni ko'rsatish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    locations = db.get_latest_locations(limit=20)
    
    if not locations:
        await message.answer("📭 Hech qanday joylashuv yo'q.")
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    text = "📍 <b>BARCHA JOYLASHUVLAR:</b>\n\n"
    
    for i, loc in enumerate(locations, 1):
        location_id = loc[0]
        user_name = loc[2]
        phone = loc[3]
        status = loc[6]
        sent_time = loc[7].split()[1][:5] if isinstance(loc[7], str) else str(loc[7])[11:16]
        
        # Status ranglari
        status_icon = "🟡" if status == 'pending' else "🟢" if status == 'accepted' else "🔴"
        
        text += f"{i}. {status_icon} <b>#{location_id}</b> - {user_name}\n"
        text += f"   📞 {phone} | ⏰ {sent_time}\n"
        text += "   ─" * 15 + "\n"
    
    # Inline klaviatura
    keyboard_buttons = []
    
    for loc in locations[:5]:
        location_id = loc[0]
        user_name = loc[2]
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"📍 #{location_id} ({user_name})",
                callback_data=f"view_location:{location_id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="🔄 Yangilash",
            callback_data="refresh_locations_admin"
        ),
        InlineKeyboardButton(
            text="📤 Eng so'nggisi",
            callback_data="view_latest_location"
        )
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# Joylashuv qabul qilish rejimi
async def location_receive_mode(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    await message.answer(
        "📍 Joylashuv qabul qilish rejimi yoqildi.\n\n"
        "Endi foydalanuvchilar joylashuv yuborganida, ularning ma'lumotlari bu yerda ko'rinadi."
    )

# Asosiy menyuga qaytish
async def back_to_main_menu(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    from main import get_main_menu_keyboard
    await message.answer("🏠 Asosiy menyu", reply_markup=get_main_menu_keyboard('uz'))
    await state.clear()

# Admin buyruqlarini boshqarish
async def handle_admin_command(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    command = message.text
    current_state = await state.get_state()
    
    # ✅ BARCHA HOLATLAR STRING FORMATDA TEKSHIRILMOQDA
    
    # Bloklash holatlari
    if current_state == AdminStates.blocking_user.state:
        await process_block_user(message, state)
        return
    
    elif current_state == AdminStates.unblocking_user.state:
        await process_unblock_user(message, state)
        return
    
    # Reklama holatlari
    elif current_state == AdminStates.sending_message.state:
        await process_broadcast_type(message, state)
        return
    
    elif current_state == AdminStates.waiting_broadcast_text.state:
        await process_broadcast_text(message, state)
        return
    
    elif current_state == AdminStates.waiting_broadcast_photo.state:
        await process_broadcast_photo(message, state)
        return
    
    # Kontent qo'shish holatlari
    elif current_state == AdminStates.adding_content.state:
        await process_content_category(message, state)
        return
    
    elif current_state == AdminStates.waiting_for_content.state:
        await process_content_type(message, state)
        return
    
    elif current_state == AdminStates.waiting_for_caption.state:
        if message.content_type in ['photo', 'video', 'document']:
            await process_content_file(message, state)
        elif message.text and message.text == "🔙 Orqaga":
            await message.answer("📄 Kontent turini tanlang:", reply_markup=get_content_type_keyboard())
            await state.set_state(AdminStates.waiting_for_content)
        return
    
    # Kontent o'chirish holatlari
    elif current_state == AdminStates.deleting_content.state:
        await process_delete_category(message, state)
        return
    
    # ✅ ODDIY BUYRULAR
    if command == "📊 Foydalanuvchilar Ma'lumotlari":
        await show_users_info(message)
    
    elif command == "➕ Kontent Qo'shish":
        await start_adding_content(message, state)
    
    elif command == "📨 Xabar Yuborish":
        await start_broadcast(message, state)
    
    elif command == "🗑️ Kontent O'chirish":
        await start_deleting_content(message, state)
    
    elif command == "🚫 Bloklash":
        await start_blocking_user(message, state)
    
    elif command == "✅ Blokdan Ochish":
        await start_unblocking_user(message, state)
    
    elif command == "📋 Kontentlar Ro'yxati":
        await show_contents_list(message)
    
    elif command == "📍 Joylashuvni Ko'rish":
        await show_latest_locations(message)
    
    elif command == "🔙 Asosiy Menyuga Qaytish":
        await back_to_main_menu(message, state)
    
    # KATEGORIYA TUGMALARI
    elif command in ["🛠️ Klassik Tamirlash", "🎨 Lepka Yopishtirish", 
                    "🏠 Gipsi Carton Fason", "💻 HiTech Tamirlash",
                    "🔨 To'liq Tamirlash", "📹 Video Joylash"]:
        
        # Agar FSM holati bo'lsa
        if current_state == AdminStates.adding_content.state:
            await process_content_category(message, state)
        elif current_state == AdminStates.deleting_content.state:
            await process_delete_category(message, state)
        else:
            await message.answer("Iltimos, avval '➕ Kontent Qo'shish' yoki '🗑️ Kontent O'chirish' tugmasini bosing!")
    
    # BOSHQALAR
    elif command in ["🖼️ Rasm", "📹 Video", "📄 Dokument", "🔙 Orqaga",
                    "📝 Matnli reklama", "🖼️ Rasmli reklama", 
                    "📹 Videoli reklama", "📄 Dokument reklama"]:
        
        if current_state == AdminStates.waiting_for_content.state:
            await process_content_type(message, state)
        elif command == "🔙 Orqaga":
            await state.clear()
            await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
    
    # Agar hech qaysi shart bajarilmasa
    else:
        await message.answer("❌ Noma'lum buyruq!", reply_markup=get_admin_keyboard())