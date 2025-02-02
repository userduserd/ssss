import asyncio
import random
from aiogram import Router, Bot, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from .text import add_balance_text, choose_payment_balance, confirm_balance_add, waiting_for_pay, \
    add_balance_for_exchanger, confirm_cancel_now, order_text, invoice_canceled
from .utils import CheckState, check_invoice_paid, create_usdt_invoice, check_invoice, get_req, parse_number
from tg.models import TelegramUser, City, Rayon, Product, GramPrice, Invoice, Req
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async

router = Router()


class BalanceState(StatesGroup):
    awaiting_amount = State()


@router.callback_query(F.data == "add_balance")
async def add_balance(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BalanceState.awaiting_amount)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="back_to_menu"))
    await callback.message.edit_text(add_balance_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.message(BalanceState.awaiting_amount)
async def balance_awaiting_amount(msg: Message, state: FSMContext):
    try:
        amount = parse_number(msg.text)
        if amount >= 1000:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="Банки KZ", callback_data=f"choose_payment_bank_{amount}"))
            builder.add(InlineKeyboardButton(text="USDT TRC20", callback_data=f"choose_payment_usdt_{amount}"))
            builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="add_balance"))
            builder.adjust(1)
            await msg.answer(choose_payment_balance.format(amount=amount), parse_mode="Markdown", reply_markup=builder.as_markup())
            await state.clear()
        else:
            text = ("💰 Пополнение баланса\n\n"
                    "Минимальная сумма пополнения 1000*₸* :")
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="back_to_menu"))
            await msg.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    except Exception as e:
        print(e)


@router.callback_query(F.data.startswith("choose_payment_"))
async def choose_payment_method(callback: CallbackQuery):
    data = callback.data.split("_")
    amount = data[3]
    method = data[2]
    text = confirm_balance_add.format(amount=amount, method=method)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Подтвердить", callback_data=f"balance_add_{method}_{amount}"))
    builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="back_to_menu"))
    builder.adjust(1)
    await callback.message.edit_text(text=text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.callback_query(F.data.startswith("balance_add_bank_"))
async def balance_add_confirm(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = callback.data.split("_")
    amount = data[3]
    method = data[2]
    amount = int(amount)+random.randint(1,30)
    bot_user = await bot.get_me()
    bot_user = bot_user.username
    req, unique_id = await get_req(amount, bot_user)
    user = await sync_to_async(TelegramUser.objects.get)(user_id=callback.from_user.id)
    invoice = await sync_to_async(Invoice.objects.filter)(user=user, active=True)
    if not invoice:
        invoice = await sync_to_async(Invoice.objects.create)(user=user, req=req, kzt_amount=amount,
                                                              method=method, unique_pod=unique_id)
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🚫 Отменить", callback_data=f"conf_cancel_{invoice.id}"))
        builder.adjust(1)
        text = waiting_for_pay.format(order_id=invoice.id, req=invoice.req, amount=invoice.kzt_amount if invoice.method == 'bank' else invoice.crypto_amount,
                                  symb=f"{'$' if invoice.method == 'usdt' else '₸'}", method=invoice.method)
        text += ("\n\n‼️ Если вы оплатили, но бот не увидел Вашу оплату, перешлите данное сообщение и чек об оплате - @PDDRJKA_bot"
                 f"ID заявки: `{unique_id}`")
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="⚙️ Поддержка по оплате", url="https://t.me/PDDRJKA_bot"))
        await callback.message.answer(req, reply_markup=builder.as_markup())
        asyncio.create_task(check_invoice_paid(callback.message, invoice, user))


@router.callback_query(F.data.startswith("balance_add_usdt_"))
async def balance_add_bank(call: CallbackQuery):
    data = call.data.split("_")
    amount = data[3]
    method = data[2]
    user = await sync_to_async(TelegramUser.objects.get)(user_id=call.from_user.id)
    invoice = await sync_to_async(Invoice.objects.filter)(user=user, active=True)
    if not invoice:
        amount = int(amount) + random.randint(1, 50)
        invoice_info, usdt_price = await create_usdt_invoice(amount)
        req = invoice_info["address"]
        invoice_id = invoice_info["invoice"]
        usdt_price += 0.1
        usdt_price = round(usdt_price, 4)
        invoice = await sync_to_async(Invoice.objects.create)(user=user, req=req,
                                                              kzt_amount=amount, crypto_amount=usdt_price, method=method)
        text = waiting_for_pay.format(amount=usdt_price, req=invoice.req, method=method, symb="$")
        asyncio.create_task(check_invoice(invoice_id, call.message, user, amount, invoice))
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🚫 Отменить", callback_data=f"conf_cancel_{invoice.id}"))
        builder.adjust(1)
        await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.callback_query(F.data.startswith("conf_cancel_"))
async def confirm_cancel(callback: CallbackQuery):
    data = callback.data.split("_")
    inv_id = data[2]
    invoice = await sync_to_async(Invoice.objects.get)(id=inv_id)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Да", callback_data=f"cancel_{invoice.id}"))
    builder.add(InlineKeyboardButton(text="Нет", callback_data=f"back_to_order"))
    builder.adjust(2)
    await callback.message.edit_text(confirm_cancel_now, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.callback_query(F.data == "back_to_order")
async def back_to_order(callback: CallbackQuery):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=callback.from_user.id)
    invoice = await sync_to_async(Invoice.objects.filter)(user=user, active=True)
    invoice = invoice.first()
    if invoice is None:
        return
    text = waiting_for_pay.format(order_id=invoice.id, req=invoice.req, amount=invoice.kzt_amount if invoice.method == 'bank' else invoice.crypto_amount,
                                  symb=f"{'$' if invoice.method == 'usdt' else '₸'}", method=invoice.method)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🚫 Отменить", callback_data=f"conf_cancel_{invoice.id}"))
    builder.adjust(1)
    await callback.message.edit_text(text=text, parse_mode="Markdown", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("cancel_"))
async def cancel_invoice(callback: CallbackQuery):
    invoice_id = callback.data.split("_")[1]
    invoice = await sync_to_async(Invoice.objects.get)(id=invoice_id)
    invoice.active = False
    invoice.save()
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="‹ На главную", callback_data="main_menu"))
    await callback.message.edit_text(invoice_canceled, reply_markup=builder.as_markup(), parse_mode="Markdown")
    return