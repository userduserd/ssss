from aiogram import Router, Bot, F
from aiogram.types import  InlineKeyboardButton, CallbackQuery
from .text import  ref_text
from tg.models import TelegramUser, Invoice, Text, PromoCode, ShopConfiguration
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async

router = Router()

@router.callback_query(F.data == "ref")
async def refs(call: CallbackQuery, bot: Bot):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=call.from_user.id)
    bot_info = await bot.get_me()
    bot_user = bot_info.username
    escaped_bot_user = bot_user.replace("_", "\\_")
    link = f"t.me/{escaped_bot_user}?start={user.referral_code}"
    ref_count = await sync_to_async(user.referrals.count)()
    conf = await sync_to_async(ShopConfiguration.objects.first)()
    if not conf:
        conf = await sync_to_async(ShopConfiguration.objects.create)()
    text = ref_text.format(link=link, count=ref_count, prc=conf.ref_percent)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="‹ Назад", callback_data="back_to_menu"))
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")