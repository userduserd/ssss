from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandObject, BaseFilter
from aiogram.types import Message, InlineKeyboardButton, ReplyKeyboardMarkup, ChatMemberOwner, ChatMemberAdministrator, \
    KeyboardButton, CallbackQuery
from .kb import menu
from .text import menu_text, waiting_for_pay
from tg.models import TelegramUser, Invoice, Text
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
from aiogram.fsm.context import FSMContext

from .utils import CheckState

router = Router()


class ActiveInvoiceFilter(BaseFilter):
    async def __call__(self, msg: Message, state: FSMContext) -> bool:
        user_id = msg.from_user.id
        user, created = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=user_id)
        has_active_invoice = await sync_to_async(Invoice.objects.filter)(user=user, active=True)
        has_active_invoice.exists()
        if msg.photo or msg.document:
            return False
        if has_active_invoice:
            return True
        if not user:
            return False


@router.message(ActiveInvoiceFilter())
async def active_invoice_handler(msg: Message, state: FSMContext, bot: Bot):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    invoice = await sync_to_async(Invoice.objects.filter)(user=user, active=True)
    invoice = invoice.first()
    if invoice is None:
        return
    text = waiting_for_pay.format(order_id=invoice.id, req=invoice.req, amount=invoice.kzt_amount if invoice.method == 'bank' else invoice.crypto_amount,
                                  symb=f"{'$' if invoice.method == 'usdt' else '₸'}", method=invoice.method)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🚫 Отменить", callback_data=f"conf_cancel_{invoice.id}"))
    builder.adjust(1)
    await state.set_state(CheckState.awaiting_check)
    await msg.answer(text=text, parse_mode="Markdown", reply_markup=builder.as_markup())


class ActiveInvoiceCallbackFilter(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        if callback.data.startswith("conf_cancel_"):
            return False
        if callback.data.startswith("cancel_"):
            return False
        if callback.data.startswith("back_to_order"):
            return False
        user_id = callback.from_user.id
        user = await sync_to_async(TelegramUser.objects.filter)(user_id=user_id)
        if not user.exists():
            return False
        has_active_invoice = await sync_to_async(Invoice.objects.filter)(user=user.first(), active=True)
        return has_active_invoice.exists()


@router.callback_query(ActiveInvoiceCallbackFilter())
async def block_buttons_handler(callback: CallbackQuery, bot: Bot):
    await callback.answer("Закончите пополнение по заявке или отмените её")


@router.message(F.text == "ℹ️ Показать меню")
async def main_menu(msg: Message):
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=msg.from_user.id)
    user.first_name = msg.from_user.first_name
    user.last_name = msg.from_user.last_name
    user.username = msg.from_user.username
    user.save()
    await msg.answer(menu_text.format(balance=user.balance), reply_markup=menu, parse_mode="Markdown")


@router.message(Command("start"))
async def start(msg: Message, command: CommandObject, edit=None):
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=msg.from_user.id)
    user.first_name = msg.from_user.first_name
    user.last_name = msg.from_user.last_name
    user.username = msg.from_user.username
    user.save()
    args = command.args
    if args:
        ref_by = await sync_to_async(TelegramUser.objects.filter)(referral_code=args)
        if ref_by:
            ref_by = ref_by.first()
            if not user.referred_by and user != ref_by:
                user.referred_by = ref_by
                user.save()
    menu_button = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="ℹ️ Показать меню")]])
    text = await sync_to_async(Text.objects.first)()
    if text:
        await msg.answer(text.welcome, reply_markup=menu_button, parse_mode="Markdown")
        await msg.answer(menu_text.format(balance=user.balance), reply_markup=menu, parse_mode="Markdown")
    else:
        await msg.answer("☀️ *Приветствие*", reply_markup=menu_button, parse_mode="Markdown")
        await msg.answer(menu_text.format(balance=user.balance), reply_markup=menu, parse_mode="Markdown")



@router.callback_query(F.data == "main_menu")
async def main_start(callback: CallbackQuery, edit=None):
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=callback.from_user.id)
    user.first_name = callback.from_user.first_name
    user.last_name = callback.from_user.last_name
    user.username = callback.from_user.username
    user.save()
    await callback.message.edit_text(menu_text.format(balance=user.balance), reply_markup=menu, parse_mode="Markdown")
