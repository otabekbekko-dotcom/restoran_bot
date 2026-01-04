import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_ID
from database import Database

# Logging sozlash
logging.basicConfig(level=logging.INFO)

# Bot va dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database()

# Savat uchun global dictionary
user_carts = {}

# States
class OrderStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_payment = State()

# Asosiy menu
def main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Buyurtma berish")],
            [KeyboardButton(text="📋 Savat"), KeyboardButton(text="ℹ️ Ma'lumot")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Kategoriyalar
def categories_menu():
    categories = db.get_categories()
    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(text=cat[1], callback_data=f"cat_{cat[0]}")])
    buttons.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Mahsulotlar
def products_menu(category_id):
    products = db.get_products_by_category(category_id)
    buttons = []
    for prod in products:
        buttons.append([InlineKeyboardButton(
            text=f"{prod[1]} - {prod[2]:,} so'm", 
            callback_data=f"prod_{prod[0]}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_categories")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Mahsulot tafsilotlari
def product_detail_menu(product_id):
    buttons = [
        [InlineKeyboardButton(text="➕ Savatga qo'shish", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_products")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# /start buyrug'i
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_carts[message.from_user.id] = []
    await message.answer(
        f"👋 Assalomu aleykum, {message.from_user.full_name}!\n\n"
        "🍕 Demo Restoran botiga xush kelibsiz!\n\n"
        "Buyurtma berish uchun tugmani bosing 👇",
        reply_markup=main_menu()
    )

# Buyurtma berish
@dp.message(F.text == "🛒 Buyurtma berish")
async def order_start(message: types.Message):
    await message.answer(
        "Kategoriyani tanlang:",
        reply_markup=categories_menu()
    )

# Kategoriya tanlash
@dp.callback_query(F.data.startswith("cat_"))
async def category_selected(callback: types.CallbackQuery):
    category_id = int(callback.data.split("_")[1])
    await callback.message.edit_text(
        "Mahsulotni tanlang:",
        reply_markup=products_menu(category_id)
    )
    await callback.answer()

# Mahsulot tanlash
@dp.callback_query(F.data.startswith("prod_"))
async def product_selected(callback: types.CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    product = db.get_product(product_id)
    
    text = (
        f"📦 {product[1]}\n\n"
        f"💰 Narxi: {product[2]:,} so'm\n"
        f"📝 {product[4]}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=product_detail_menu(product_id)
    )
    await callback.answer()

# Savatga qo'shish
@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: types.CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    if user_id not in user_carts:
        user_carts[user_id] = []
    
    product = db.get_product(product_id)
    user_carts[user_id].append({
        'id': product[0],
        'name': product[1],
        'price': product[2]
    })
    
    await callback.answer("✅ Savatga qo'shildi!", show_alert=True)
    await callback.message.edit_text(
        f"✅ {product[1]} savatga qo'shildi!\n\n"
        "Yana mahsulot qo'shish yoki savatni ko'rish uchun tugmalardan foydalaning.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Mahsulotlarga qaytish", callback_data="back_to_categories")],
            [InlineKeyboardButton(text="📋 Savatni ko'rish", callback_data="view_cart")]
        ])
    )

# Savatni ko'rish
@dp.message(F.text == "📋 Savat")
@dp.callback_query(F.data == "view_cart")
async def view_cart(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    
    if user_id not in user_carts or len(user_carts[user_id]) == 0:
        text = "🛒 Savatingiz bo'sh"
        if isinstance(event, types.CallbackQuery):
            await event.message.edit_text(text)
            await event.answer()
        else:
            await event.answer(text)
        return
    
    cart = user_carts[user_id]
    total = sum(item['price'] for item in cart)
    
    text = "🛒 Savatingiz:\n\n"
    for idx, item in enumerate(cart, 1):
        text += f"{idx}. {item['name']} - {item['price']:,} so'm\n"
    text += f"\n💰 Jami: {total:,} so'm"
    
    buttons = [
        [InlineKeyboardButton(text="✅ Buyurtmani tasdiqlash", callback_data="confirm_order")],
        [InlineKeyboardButton(text="🗑 Savatni tozalash", callback_data="clear_cart")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="back_to_main")]
    ]
    
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        await event.answer()
    else:
        await event.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

# Savatni tozalash
@dp.callback_query(F.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    user_carts[callback.from_user.id] = []
    await callback.message.edit_text("🗑 Savat tozalandi")
    await callback.answer()

# Buyurtmani tasdiqlash
@dp.callback_query(F.data == "confirm_order")
async def confirm_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📱 Telefon raqamingizni yuboring:\n"
        "(Masalan: +998901234567)"
    )
    await state.set_state(OrderStates.waiting_for_phone)
    await callback.answer()

# Telefon qabul qilish
@dp.message(OrderStates.waiting_for_phone)
async def phone_received(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    
    buttons = [
        [InlineKeyboardButton(text="💵 Naqd", callback_data="pay_cash")],
        [InlineKeyboardButton(text="💳 Karta", callback_data="pay_card")]
    ]
    
    await message.answer(
        "💳 To'lov turini tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.set_state(OrderStates.waiting_for_payment)

# To'lov turi
@dp.callback_query(F.data.startswith("pay_"))
async def payment_selected(callback: types.CallbackQuery, state: FSMContext):
    payment_method = "Naqd" if callback.data == "pay_cash" else "Karta"
    user_data = await state.get_data()
    user_id = callback.from_user.id
    
    cart = user_carts.get(user_id, [])
    total = sum(item['price'] for item in cart)
    
    # Buyurtmani bazaga saqlash
    order_id = db.create_order(
        user_id=user_id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name,
        phone=user_data['phone'],
        items=cart,
        total=total,
        payment_method=payment_method
    )
    
    # Foydalanuvchiga xabar
    await callback.message.edit_text(
        f"✅ Buyurtma qabul qilindi!\n\n"
        f"📝 Buyurtma raqami: #{order_id}\n"
        f"💰 Jami: {total:,} so'm\n"
        f"💳 To'lov: {payment_method}\n\n"
        "Tez orada siz bilan bog'lanamiz!"
    )
    
    # Adminga xabar
    admin_text = (
        f"🔔 Yangi buyurtma!\n\n"
        f"📝 Buyurtma #{order_id}\n"
        f"👤 {callback.from_user.full_name}\n"
        f"📱 {user_data['phone']}\n"
        f"💰 Summa: {total:,} so'm\n"
        f"💳 To'lov: {payment_method}\n\n"
        "📦 Mahsulotlar:\n"
    )
    for idx, item in enumerate(cart, 1):
        admin_text += f"{idx}. {item['name']} - {item['price']:,} so'm\n"
    
    try:
        await bot.send_message(ADMIN_ID, admin_text)
    except:
        pass
    
    # Savatni tozalash
    user_carts[user_id] = []
    await state.clear()
    await callback.answer()

# Ma'lumot
@dp.message(F.text == "ℹ️ Ma'lumot")
async def info(message: types.Message):
    await message.answer(
        "ℹ️ Demo Restoran Bot\n\n"
        "Bu bot orqali siz:\n"
        "✅ Mahsulotlarni ko'rishingiz\n"
        "✅ Buyurtma berishingiz\n"
        "✅ To'lov turini tanlashingiz mumkin\n\n"
        "📞 Aloqa: +998 90 123 45 67"
    )

# Ortga qaytish
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=main_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Kategoriyani tanlang:",
        reply_markup=categories_menu()
    )
    await callback.answer()

# Admin buyruqlari
@dp.message(Command("orders"))
async def show_orders(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    orders = db.get_all_orders()
    if not orders:
        await message.answer("Buyurtmalar yo'q")
        return
    
    text = "📋 Barcha buyurtmalar:\n\n"
    for order in orders[:10]:  # Oxirgi 10 ta
        text += f"#{order[0]} - {order[3]} - {order[6]:,} so'm - {order[7]}\n"
    
    await message.answer(text)

# Botni ishga tushirish
async def main():
    print("Bot ishga tushdi! ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())