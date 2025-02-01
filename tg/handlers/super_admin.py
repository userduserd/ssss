import asyncio
import random
from tempfile import NamedTemporaryFile
from aiogram import Router, Bot, F
from aiogram.types import Message, InlineKeyboardButton, ReplyKeyboardMarkup, ChatMemberOwner, ChatMemberAdministrator, \
    KeyboardButton, CallbackQuery, InputFile, FSInputFile
from aiogram.fsm.context import FSMContext
from django.utils import timezone
from aiogram.filters import Filter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from django.db.models import Sum
from .kb import menu_keyboard, menu
from .start import start
from .text import menu_text, magazine_text, geo_text, payment_text, confirm_text, order_text, confirm_cancel_now, \
    invoice_canceled, check_information, transactions_text
from .utils import CheckState
from django.db.models import Q, Count
from tg.models import TelegramUser, City, Rayon, Product, GramPrice, Invoice, Req, WithdrawInvoices
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from asgiref.sync import sync_to_async



router = Router()

class IsSuperAdminFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        try:
            user = await sync_to_async(TelegramUser.objects.get)(user_id=message.from_user.id)
            return user.is_super_admin
        except TelegramUser.DoesNotExist:
            return False

router.message.filter(IsSuperAdminFilter())

class WithdrawState(StatesGroup):
    awaiting_course = State()
    awaiting_txid = State()

@router.callback_query(F.data.startswith("super_admin_withdraw_"))
async def super_admin_withdraw(call: CallbackQuery, state: FSMContext):
    data = call.data.split("_")
    withdraw_id = data[3]
    user_id = data[4]
    await state.set_state(WithdrawState.awaiting_course)
    await state.update_data(withdraw_id=withdraw_id, user_id=user_id)
    await call.message.answer("Введите курс USDT")

@router.message(WithdrawState.awaiting_course)
async def awaiting_usdt_course(msg: Message, state: FSMContext):
    try:
        course = int(msg.text)
        data = await state.get_data()
        withdraw_id = data.get("withdraw_id")
        withdraw_requests = await sync_to_async(WithdrawInvoices.objects.get)(id=withdraw_id)
        invoices = await sync_to_async(withdraw_requests.invoices_to_withdraw.all)()
        total_kzt_amount = sum(invoice.kzt_amount for invoice in invoices)
        withdraw_kzt_amount = total_kzt_amount / 100 * 90
        kzt_amount = total_kzt_amount / 100 * 90
        withdraw_usdt_amount = withdraw_kzt_amount / course
        our_coms = (total_kzt_amount / course) - withdraw_usdt_amount
        text = (f"Отправить {round(withdraw_usdt_amount, 4)}\n"
                f"У нас остается: {round(our_coms, 4)}\n"
                f"Отправьте TXID отправки")
        await state.update_data(course=course, usdt_amount=withdraw_usdt_amount, kzt_amount=kzt_amount)
        await msg.answer(text)
        await state.set_state(WithdrawState.awaiting_txid)
    except Exception as e:
        print(e)

@router.message(WithdrawState.awaiting_txid)
async def awaiting_txid(msg: Message, state: FSMContext, bot: Bot):
    try:
        txid = msg.text
        data = await state.get_data()
        withdraw_id = data.get("withdraw_id")
        user_id = data.get("user_id")
        course = data.get("course")
        usdt_amount = data.get("usdt_amount")
        kzt_amount = data.get("kzt_amount")
        withdraw_request = await sync_to_async(WithdrawInvoices.objects.get)(id=withdraw_id)
        withdraw_invoices = withdraw_request.invoices_to_withdraw.all()
        for i in withdraw_invoices:
            i.withdrawed_to_shop = True
            i.txid_withdrawed_to_shop = txid
            i.save()
        withdraw_request.complete = True
        withdraw_request.save()
        text = transactions_text.format(usdt_sum=round(usdt_amount, 4), kzt_sum=round(kzt_amount, 4), txid=txid, course=course)
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="‹ Админ панель", callback_data="back_to_admin_menu"))
        await bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown", reply_markup=builder.as_markup())
    except Exception as e:
        print(e)