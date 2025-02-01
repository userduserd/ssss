import asyncio
import random
from tempfile import NamedTemporaryFile
from aiogram import Router, Bot, F
from aiogram.types import Message, InlineKeyboardButton, ReplyKeyboardMarkup, ChatMemberOwner, ChatMemberAdministrator, \
    KeyboardButton, CallbackQuery, InputFile, FSInputFile
from aiogram.fsm.context import FSMContext
from django.utils import timezone

from .kb import menu_keyboard, menu
from .start import start
from .text import menu_text, magazine_text, geo_text, payment_text, confirm_text, order_text, confirm_cancel_now, \
    invoice_canceled, check_information
from .utils import CheckState
from django.db.models import Q, Count
from tg.models import TelegramUser, City, Rayon, Product, GramPrice, Invoice, Req
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from asgiref.sync import sync_to_async
router = Router()


@router.callback_query(F.data.startswith("exchange_invoice_paid_"))
async def exchange_invoice_paid(callback: CallbackQuery, bot: Bot):
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=callback.from_user.id)
    if user.is_exchanger:
        data = callback.data.split("_")
        invoice_id = data[3]
        invoice = await sync_to_async(Invoice.objects.get)(id=invoice_id)
        if not invoice.complete and invoice.active:
            invoice.complete = True
            invoice.active = False
            invoice.save()
            invoice.user.balance += invoice.amount
            invoice.user.save()

            await bot.send_message(chat_id=invoice.user.user_id, text=f"💸 *Ваш баланс пополнен на *{invoice.amount}*₸*",
                                   parse_mode="Markdown")
            await callback.message.answer(f"Заявка #{invoice.id}\n✅ Обработано ✅")
        else:
            await callback.answer("Заявка уже обработана или просрочена!")


@router.callback_query(F.data.startswith("exchange_invoice_notpaid_"))
async def exchange_invoice_not_paid(callback: CallbackQuery, bot: Bot):
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=callback.from_user.id)
    if user.is_exchanger:
        data = callback.data.split("_")
        invoice_id = data[3]
        invoice = await sync_to_async(Invoice.objects.get)(id=invoice_id)
        if not invoice.complete and invoice.active:
            invoice.reserved_product.reserved = False
            invoice.active = False
            invoice.save()
            invoice.reserved_product.save()
            await bot.send_message(chat_id=invoice.user.user_id, text="🔘 *Заявка отменена!*", parse_mode="Markdown")
            await callback.message.answer(f"Заявка #{invoice.id}\n🟡 Отменена 🟡")
        else:
            await callback.answer("Заявка уже обработана или просрочена!")