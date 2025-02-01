from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandObject, BaseFilter
from aiogram.types import Message, InlineKeyboardButton, ReplyKeyboardMarkup, ChatMemberOwner, ChatMemberAdministrator, \
    KeyboardButton, CallbackQuery
from .kb import menu
from .text import menu_text, waiting_for_pay, promo_text, activating_promo, denied_promo
from tg.models import TelegramUser, Invoice, Text, PromoCode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from .utils import CheckState

router = Router()

class PromoState(StatesGroup):
    awaiting_promo = State()


@router.callback_query(F.data == "add_promo")
async def active_promo(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💊 Активировать промокод", callback_data="activate_promo"))
    builder.row(InlineKeyboardButton(text="‹ Назад", callback_data="back_to_menu"))
    await call.message.edit_text(promo_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data == "activate_promo")
async def activate_promo(call: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🚫 Отменить", callback_data="add_promo"))
    await state.set_state(PromoState.awaiting_promo)
    await call.message.edit_text(activating_promo, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.message(PromoState.awaiting_promo)
async def awaiting_promo(msg: Message, state: FSMContext):
    try:
        promo = await sync_to_async(PromoCode.objects.get)(code=msg.text)
        if promo:
            if promo.active:
                user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
                user.balance += promo.amount
                promo.active = False
                promo.user = user
                promo.save()
                user.save()
                await msg.answer(f"➕ _Ваш баланс пополнен на_ `{promo.amount}` *₸*")
            else:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(text="‹ На главную", callback_data="back_to_menu"))
                await msg.answer(denied_promo, reply_markup=builder.as_markup(), parse_mode="Markdown")
    except Exception:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="‹ На главную", callback_data="back_to_menu"))
        await msg.answer(denied_promo, reply_markup=builder.as_markup(), parse_mode="Markdown")

