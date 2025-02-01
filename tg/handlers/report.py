from aiogram import Router, Bot, F
from aiogram.types import Message, InlineKeyboardButton, ReplyKeyboardMarkup, ChatMemberOwner, ChatMemberAdministrator, \
    KeyboardButton, CallbackQuery, InputFile, FSInputFile
from aiogram.fsm.context import FSMContext
from django.utils import timezone

from .kb import menu
from .text import menu_text, magazine_text, geo_text, payment_text, confirm_text, confirm_cancel_now, \
    invoice_canceled, check_accepted, waiting_for_pay, \
    add_balance_for_exchanger
from .utils import CheckState
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from tg.models import TelegramUser, City, Rayon, Product, GramPrice, Invoice, Req, Chapter, ShopConfiguration, Report, Conversation
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from asgiref.sync import sync_to_async

router = Router()

class ReportState(StatesGroup):
    awaiting_report_msg = State()

@router.callback_query(F.data.startswith("ticket_problem_"))
async def ticket_problem(call: CallbackQuery, state: FSMContext):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=call.from_user.id)
    data = call.data.split("_")
    await state.update_data(product_id=data[2])
    await state.set_state(ReportState.awaiting_report_msg)
    text = "🎈 *Проблема с заказом*\n\nНапишите в кратции причину обращения:"
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="‹ Главное меню", callback_data="back_to_menu"))
    await call.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.message(ReportState.awaiting_report_msg)
async def awaiting_report_msg(msg: Message, state: FSMContext):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    data = await state.get_data()
    product_id = data.get("product_id")
    product = await sync_to_async(Product.objects.get)(id=product_id)
    new_report = await sync_to_async(Report.objects.create)(user=user, product=product)
    new_conversation = await sync_to_async(Conversation.objects.create)(report=new_report, user=user, text=msg.text)




