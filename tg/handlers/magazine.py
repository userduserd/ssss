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
from tg.models import TelegramUser, City, Rayon, Product, GramPrice, Invoice, Req, Chapter, ShopConfiguration
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from asgiref.sync import sync_to_async

router = Router()


@router.callback_query(F.data == "start_buy")
async def magazine(callback: CallbackQuery, bot: Bot):
    cities = await sync_to_async(City.objects.all)()
    builder = InlineKeyboardBuilder()
    if cities:
        for i in cities:
            builder.add(InlineKeyboardButton(text=f"🏙️ {i.city_name} 🏙️", callback_data=f"city_{i.id}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="‹ Назад", callback_data="back_to_menu"))

    await callback.message.edit_text(magazine_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.callback_query(F.data.startswith("city_"))
async def cities(callback: CallbackQuery):
    data = callback.data.split("_")
    city = await sync_to_async(City.objects.get)(id=data[1])
    gram_with_products = await sync_to_async(GramPrice.objects.filter)(product__isnull=False,
                                                                      product__bought_by__isnull=True,
                                                                      product__reserved=False,
                                                                      product__city=city)
    gram_with_products = gram_with_products.distinct()

    builder = InlineKeyboardBuilder()
    for gram in gram_with_products:
        button_text = f"{gram.chapter.chapter_name} - {gram.gram}г - {gram.price}₸"
        builder.add(InlineKeyboardButton(text=button_text, callback_data=f"gram_{city.id}_{gram.id}"))

    builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="start_buy"))
    builder.adjust(1)

    await callback.message.edit_text(geo_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=callback.from_user.id)
    user.first_name = callback.from_user.first_name
    user.last_name = callback.from_user.last_name
    user.username = callback.from_user.username
    user.save()
    await state.clear()
    await callback.message.edit_text(menu_text.format(balance=user.balance), reply_markup=menu, parse_mode="Markdown")


@router.callback_query(F.data.startswith("gram_"))
async def choose_gram(callback: CallbackQuery, bot: Bot):
    data = callback.data.split("_")
    city_id = data[1]
    gram_id = data[2]
    city = await sync_to_async(City.objects.get)(id=city_id)
    gram = await sync_to_async(GramPrice.objects.get)(id=gram_id)
    geo_with_products = await sync_to_async(Rayon.objects.filter)(product__isnull=False,
                                                                  product__bought_by__isnull=True,
                                                                  product__reserved=False,
                                                                  city=city, gram=gram)
    geo_with_products = geo_with_products.distinct()
    builder = InlineKeyboardBuilder()
    for geo in geo_with_products:
        builder.add(InlineKeyboardButton(text=f"📍 {geo.rayon_name} 🌳", callback_data=f"trybuy_{geo.id}_{gram.id}"))
    builder.add(InlineKeyboardButton(text="‹ Назад", callback_data=f"city_{city.id}"))
    builder.adjust(1)
    text = payment_text.format(geo=city.city_name, product=gram.chapter.chapter_name)
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.callback_query(F.data.startswith("trybuy_"))
async def kzt_payment(callback: CallbackQuery, bot: Bot):
    data = callback.data.split("_")
    geo_id = data[1]
    gram_id = data[2]
    geo = await sync_to_async(Rayon.objects.get)(id=geo_id)
    gram = await sync_to_async(GramPrice.objects.get)(id=gram_id)
    text = confirm_text.format(geo=geo.rayon_name, product=gram.chapter.chapter_name, gram=gram.gram, price=gram.price)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm_{geo.id}_{gram.id}"))
    if gram.chapter.photo or gram.chapter.description:
        builder.add(InlineKeyboardButton(text="Описание", callback_data=f"show_description_{gram.chapter.id}"))
    builder.add(InlineKeyboardButton(text="‹ Назад", callback_data=f"gram_{geo.city.id}_{gram.id}"))
    builder.adjust(1)
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.callback_query(F.data.startswith("show_description_"))
async def show_desc_or_photo(callback: CallbackQuery, bot: Bot):
    data = callback.data.split("_")
    chapter = await sync_to_async(Chapter.objects.get)(id=data[2])
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(user_id=callback.from_user.id)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_msg_description"))
    if chapter.photo and chapter.description:
        await bot.send_photo(chat_id=user.user_id, photo=chapter.photo, caption=chapter.description, reply_markup=builder.as_markup())
    elif chapter.photo and not chapter.description:
        await bot.send_photo(chat_id=user.user_id, photo=chapter.photo, reply_markup=builder.as_markup())
    elif chapter.description and not chapter.photo:
        await bot.send_message(chat_id=user.user_id, text=chapter.description, reply_markup=builder.as_markup())


@router.callback_query(F.data == "delete_msg_description")
async def delete_msg_description(callback: CallbackQuery):
    await callback.message.delete()


@router.callback_query(F.data.startswith("confirm_"))
async def confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=callback.from_user.id)
    data = callback.data.split("_")
    geo_id = data[1]
    gram_id = data[2]
    geo = await sync_to_async(Rayon.objects.get)(id=geo_id)
    gram = await sync_to_async(GramPrice.objects.get)(id=gram_id)
    if user.balance >= gram.price:
        products = await sync_to_async(Product.objects.filter)(rayon=geo, gram=gram, reserved=False, bought_by__isnull=True)
        products = products.order_by("?")
        product = products.first()
        if product:
            user.balance -= gram.price
            user.save()
            product.bought_by = user
            product.date_bought = timezone.now()
            product.save()
            await callback.message.delete()
            # builder = InlineKeyboardBuilder()
            # builder.add(InlineKeyboardButton(text="Проблема с заказом", callback_data=f"ticket_problem_{product.id}"))
            await callback.message.answer(f"{product.address}")
            if user.referred_by:
                shop_conf = await sync_to_async(ShopConfiguration.objects.first)()
                if shop_conf:
                    prc = shop_conf.ref_percent
                    ref_add_balance = gram.price / 100 * prc
                    user.referred_by.balance += ref_add_balance
                    user.referred_by.save()
        else:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="‹ Назад в Главное меню", callback_data="back_to_menu"))
            await callback.message.edit_text("Выбранный товар закончился.", reply_markup=builder.as_markup())
    else:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="➕ Пополнить баланс", callback_data="add_balance"))
        await callback.message.answer("На твоем балансе недостаточно средств.", reply_markup=builder.as_markup())


@router.message(CheckState.awaiting_check)
async def awaiting_check(msg: Message, state: FSMContext, bot: Bot):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    invoice = await sync_to_async(Invoice.objects.filter)(user=user, active=True)
    invoice = invoice.first()
    if msg.photo or msg.document:
        if invoice:
            check = await msg.forward("-4769514909")
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="✅ Платеж поступил", callback_data=f"exchange_invoice_paid_{invoice.id}"))
            builder.adjust(2)
            await bot.send_message(chat_id="-4769514909", text=add_balance_for_exchanger.format(inv_id=invoice.id, amount=invoice.amount, req_name=invoice.req.req_name, req=invoice.req.req), reply_to_message_id=check.message_id, parse_mode="Markdown", reply_markup=builder.as_markup())
            await msg.answer(check_accepted, parse_mode="Markdown")
        else:
            await state.clear()


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
    if not invoice:
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
    if invoice.complete:
        return
    invoice.active = False
    invoice.save()
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="‹ На главную", callback_data="main_menu"))
    await callback.message.edit_text(invoice_canceled, reply_markup=builder.as_markup(), parse_mode="Markdown")



