import asyncio
import random
from aiogram import Router, F
from aiogram.types import InlineKeyboardButton, CallbackQuery
from .text import product_text
from tg.models import TelegramUser, City, Rayon, Product, GramPrice, Invoice, Req
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async

router = Router()

PRODUCTS_PER_PAGE = 8


@router.callback_query(F.data == "user_history")
async def user_history(call: CallbackQuery):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=call.from_user.id)
    products = await sync_to_async(list)(Product.objects.filter(bought_by=user))

    if not products:
        await call.message.answer("История покупок пуста.")
        return
    await show_products_page(call, products, page=0)


async def show_products_page(call: CallbackQuery, products, page=0):
    start = page * PRODUCTS_PER_PAGE
    end = start + PRODUCTS_PER_PAGE
    current_products = products[start:end]
    builder = InlineKeyboardBuilder()
    for product in current_products:
        builder.add(InlineKeyboardButton(
                text=f"{product.gram.chapter.chapter_name}|{product.rayon.rayon_name}|({product.date_bought:%Y-%m-%d %H:%M:%S})",
                callback_data=f"product_{product.id}",))
    builder.adjust(1)
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton(text="<<", callback_data=f"paginate:{page - 1}"))
    if end < len(products):
        pagination_buttons.append(InlineKeyboardButton(text=">>", callback_data=f"paginate:{page + 1}"))

    if pagination_buttons:
        builder.row(*pagination_buttons)
    builder.row(InlineKeyboardButton(text="‹ Назад", callback_data="back_to_menu"))
    await call.message.edit_text(
        text="Ваши покупки:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("paginate:"))
async def paginate(call: CallbackQuery):
    page = int(call.data.split(":")[1])
    user = await sync_to_async(TelegramUser.objects.get)(user_id=call.from_user.id)
    products = await sync_to_async(lambda: list(Product.objects.filter(bought_by=user)))()
    await show_products_page(call, products, page=page)


@router.callback_query(F.data.startswith("product_"))
async def show_product(call: CallbackQuery):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=call.from_user.id)
    data = call.data.split("_")
    product = await sync_to_async(Product.objects.get)(id=data[1])
    if user == product.bought_by or user.is_admin:
        text = product_text.format(city=product.city.city_name, rayon=product.rayon.rayon_name, product=product.gram.chapter.chapter_name,
                                   gram=product.gram.gram, price=product.gram.price, address=product.address)
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="❌", callback_data="delete_msg"))
        await call.message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())

@router.callback_query(F.data == "delete_msg")
async def delete_msg(call: CallbackQuery):
    await call.message.delete()