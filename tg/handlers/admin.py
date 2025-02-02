import asyncio
import pandas as pd
import aiofiles
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook
from aiogram import Router, Bot, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Filter
from aiogram.types import (Message, InlineKeyboardButton, CallbackQuery, FSInputFile, ReplyKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardRemove)

from django.db.models import Sum, Count
from aiogram.fsm.context import FSMContext
from django.db.models.functions import Coalesce
from django.db.models import Value, CharField
from .text import broadcast_text, broadcasting_text, find_user_text, profile_text, add_remove_balance_text, stat_text, \
    admin_panel_text, add_chapter_text, add_city_text, shop_configuration_text, change_ref_text, usdt_trc20_text
from .user_history import show_products_page
from .utils import vitrina_text, rassilka, terminate_process, get_total_purchases, get_total_invoices, \
    get_total_promo, get_total_promo_amount, namer, profile_shower, profile_edited_shower, get_statistics, escape_md, \
    show_desc_or_photo, escape_markdown_v2
from tg.models import TelegramUser, City, Rayon, Product, GramPrice, Invoice, Req, Chapter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
from aiogram.filters import Command
from ..models import UserBot, ShopConfiguration, WithdrawInvoices

from .kb import admin as admin_kb, admin_manage_products, admin_back_to_menu_kb, admin_statistics, conf_kb

router = Router()

class IsAdminFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        try:
            user = await sync_to_async(TelegramUser.objects.get)(user_id=message.from_user.id)
            if user.is_super_admin:
                return True
            return user.is_admin
        except TelegramUser.DoesNotExist:
            return False

router.message.filter(IsAdminFilter())

@router.message(Command("admin123"))
async def admin_panel(msg: Message):
    await msg.answer(admin_panel_text,reply_markup=admin_kb, parse_mode="Markdown")

PAGE_SIZE = 30

@router.callback_query(F.data == "personal_bots")
async def personal_bots(call: CallbackQuery):
    bots = await sync_to_async(UserBot.objects.filter)(is_active=True)
    if bots:
        total_pages = (len(bots) + PAGE_SIZE - 1) // PAGE_SIZE
        page_number = 1

        @router.callback_query(F.data.startswith("next_page_"))
        async def next_page(call: CallbackQuery):
            nonlocal page_number
            page_number += 1
            if page_number > total_pages:
                page_number = total_pages
            await send_bots_page(call, page_number, total_pages)

        @router.callback_query(F.data.startswith("prev_page_"))
        async def prev_page(call: CallbackQuery):
            nonlocal page_number
            page_number -= 1
            if page_number < 1:
                page_number = 1
            await send_bots_page(call, page_number, total_pages)

        async def send_bots_page(call: CallbackQuery, page_number: int, total_pages: int):
            start_index = (page_number - 1) * PAGE_SIZE
            end_index = min(start_index + PAGE_SIZE, len(bots))
            bots_page = bots[start_index:end_index]
            builder = InlineKeyboardBuilder()
            for bot in bots_page:
                builder.add(InlineKeyboardButton(text=f"@{(bot.bot_name)}", callback_data=f"pers_bot_{bot.id}"))
                builder.add(InlineKeyboardButton(text=f"{'🟢' if bot.is_active else '🔴'}", callback_data=f"off_bot_{bot.id}"))
            if page_number > 1:
                builder.row(InlineKeyboardButton(text="◀️ Предыдущая страница", callback_data=f"prev_page_{page_number - 1}"))
            if page_number < total_pages:
                builder.row(InlineKeyboardButton(text="Следующая страница ▶️", callback_data=f"next_page_{page_number + 1}"))
            builder.adjust(2)
            builder.row(InlineKeyboardButton(text="‹ Назад", callback_data="back_to_admin_menu"))
            await call.message.edit_text("Список ботов", reply_markup=builder.as_markup())
        await send_bots_page(call, page_number, total_pages)
    else:
        await call.message.answer("👀 _Нет подключенных ботов_", parse_mode="Markdown")


@router.callback_query(F.data.startswith("off_bot_"))
async def off_bot_admin(call: CallbackQuery):
    data = call.data.split("_")
    try:
        user_bot = await sync_to_async(UserBot.objects.get)(id=data[2])
        await terminate_process(user_bot.pid)
        await call.message.answer(f"@{user_bot.bot_name} отключен!")
        await personal_bots()
    except Exception as e:
        print(e)


@router.callback_query(F.data == "back_to_admin_menu")
async def back_to_admin_menu(call: CallbackQuery):
    await call.message.edit_text(text=admin_panel_text, reply_markup=admin_kb, parse_mode="Markdown")


@router.callback_query(F.data == "manage_products")
async def manage_products(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Manage Products", reply_markup=admin_manage_products)

@router.callback_query(F.data == "back_to_admin_panel")
async def back_to_admin_panel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(admin_panel_text, reply_markup=admin_kb, parse_mode="Markdown")

@router.callback_query(F.data == "show_products")
async def show_products(call: CallbackQuery):
    text = await vitrina_text()
    await call.message.answer(text, parse_mode="Markdown")

class BroadcastState(StatesGroup):
    awaiting_text = State()

@router.callback_query(F.data == "send_msg_to_all")
async def send_msg_to_all(call: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🚫 Отменить", callback_data="back_to_admin_panel"))
    await state.set_state(BroadcastState.awaiting_text)
    await call.message.edit_text(broadcast_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.message(BroadcastState.awaiting_text)
async def broadcast_awaiting_text(msg: Message, bot: Bot):
    b_message = await msg.answer(broadcasting_text.format(amount=0, b_amount=0, p_amount=0, p_b_amount=0), parse_mode="Markdown")
    asyncio.create_task(rassilka(b_message, msg.text, bot))

class FindUserState(StatesGroup):
    awaiting_username_user_id = State()


@router.callback_query(F.data == "manage_users")
async def manage_users(call: CallbackQuery):
    users = await sync_to_async(list)(TelegramUser.objects.all())
    if users:
        total_pages = (len(users) + PAGE_SIZE - 1) // PAGE_SIZE
        page_number = 1

        @router.callback_query(F.data.startswith("next_page_"))
        async def next_page(call: CallbackQuery):
            nonlocal page_number
            page_number += 1
            if page_number > total_pages:
                page_number = total_pages
            await send_users_page(call, page_number, total_pages)

        @router.callback_query(F.data.startswith("prev_page_"))
        async def prev_page(call: CallbackQuery):
            nonlocal page_number
            page_number -= 1
            if page_number < 1:
                page_number = 1
            await send_users_page(call, page_number, total_pages)

        async def send_users_page(call: CallbackQuery, page_number: int, total_pages: int):
            start_index = (page_number - 1) * PAGE_SIZE
            end_index = min(start_index + PAGE_SIZE, len(users))
            users_page = users[start_index:end_index]

            builder = InlineKeyboardBuilder()
            builder.row(InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="find_profile"))
            for user in users_page:
                user_name = await namer(user)
                builder.add(InlineKeyboardButton(text=f"{user_name}",callback_data=f"usershow_{user.user_id}"))
            builder.adjust(1, 2)
            if page_number > 1:
                builder.row(InlineKeyboardButton(text="◀️ Предыдущая страница",callback_data=f"prev_page_{page_number - 1}"))
            if page_number < total_pages:
                builder.row(InlineKeyboardButton(text="Следующая страница ▶️",callback_data=f"next_page_{page_number + 1}"))
            builder.row(InlineKeyboardButton(text="‹ Назад", callback_data="back_to_admin_menu"))

            await call.message.edit_text("Список пользователей:", reply_markup=builder.as_markup())

        await send_users_page(call, page_number, total_pages)
    else:
        await call.message.answer("👀 _Нет зарегистрированных пользователей_", parse_mode="Markdown")


@router.callback_query(F.data == "find_profile")
async def admin_add_balance(call: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🚫 Отменить", callback_data="back_to_admin_panel"))
    await state.set_state(FindUserState.awaiting_username_user_id)
    await call.message.edit_text(find_user_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.message(FindUserState.awaiting_username_user_id)
async def awaiting_username(msg: Message, bot: Bot, state: FSMContext):
    answer_msg = await msg.answer("🔍 Ищем пользователя...")
    message_id = answer_msg.message_id
    if msg.text.startswith("@"):
        try:
            target_user = await sync_to_async(TelegramUser.objects.get)(username__iexact=msg.text[1:])
            await profile_shower(target_user, message_id, bot, answer_msg.chat.id)
        except Exception as e:
            await msg.answer("Пользователь не найден")
    elif msg.forward_from:
        try:
            target_user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.forward_from.id)
            await profile_shower(target_user, message_id, bot, answer_msg.chat.id)
        except Exception as e:
            await answer_msg.delete()
            await msg.answer("Пользователь скрыл профиль")
    else:
        try:
            target_user_id = int(msg.text)
            target_user = await sync_to_async(TelegramUser.objects.get)(user_id=target_user_id)
            await profile_shower(target_user, message_id, bot, answer_msg.chat.id)
        except Exception as e:
            await msg.answer("Пользователь не найден")
    await state.clear()


@router.callback_query(F.data.startswith("usershow_"))
async def user_call_shower(call: CallbackQuery, state: FSMContext):
    data = call.data.split("_")
    user = await sync_to_async(TelegramUser.objects.get)(user_id=data[1])
    amount_pok = await get_total_purchases(user)
    amount_pop = await get_total_invoices(user)
    amount_promo = await get_total_promo(user)
    sum_amount_promo = await get_total_promo_amount(user)
    referred_by = "🤷"
    if user.referred_by:
        referred_by = await namer(user.referred_by)
    text = profile_text.format(user_id=user.user_id, balance=user.balance, amount_pok=amount_pok, amount_pop=amount_pop,
                               date_reg=user.created_at.strftime('%Y-%m-%d %H:%M:%S'), amount_promo=amount_promo,
                               sum_amount_promo=sum_amount_promo, ref_code=user.referral_code, ref_user=referred_by)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🛒 Покупки", callback_data=f"user_purchase_{user.user_id}"))
    builder.add(InlineKeyboardButton(text="➕➖ Баланс", callback_data=f"user_balance_{user.user_id}"))
    builder.add(InlineKeyboardButton(text=f"{'🟢' if user.is_admin else '🔴'} Администратор", callback_data=f"add_delete_admin_{user.user_id}"))
    builder.add(InlineKeyboardButton(text=f"{'❌ Заблокировать' if not user.is_banned else '✅ Разблокировать'}", callback_data=f"ban_unban_{user.user_id}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="‹ Назад", callback_data=f"manage_users"))
    await state.clear()
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.callback_query(F.data.startswith("add_delete_admin_"))
async def add_delete_admin(call: CallbackQuery):
    data = call.data.split("_")
    user = await sync_to_async(TelegramUser.objects.get)(user_id=data[3])
    if user.is_admin:
        user.is_admin = False
    elif not user.is_admin:
        user.is_admin = True
    user.save()
    await profile_edited_shower(user, call)


@router.callback_query(F.data.startswith("ban_unban_"))
async def add_delete_admin(call: CallbackQuery):
    data = call.data.split("_")
    user = await sync_to_async(TelegramUser.objects.get)(user_id=data[2])
    if user.is_banned:
        user.is_banned = False
    elif not user.is_banned:
        user.is_banned = True
    user.save()
    await profile_edited_shower(user, call)


class UserBalanceState(StatesGroup):
    awaiting_amount = State()

@router.callback_query(F.data.startswith("user_balance_"))
async def user_balance(call: CallbackQuery, state: FSMContext):
    data = call.data.split("_")
    user = await sync_to_async(TelegramUser.objects.get)(user_id=data[2])
    await state.update_data(user_id=user.user_id)
    await state.set_state(UserBalanceState.awaiting_amount)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="‹ Назад", callback_data=f"usershow_{user.user_id}"))
    await call.message.edit_text(add_remove_balance_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.message(UserBalanceState.awaiting_amount)
async def user_balance_awaiting_amount(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = data.get("user_id")
    user = await sync_to_async(TelegramUser.objects.get)(user_id=user_id)
    try:
        if msg.text.startswith("+"):
            amount = msg.text[1:]
            amount = int(amount)
            user.balance += amount
        elif msg.text.startswith("-"):
            amount = msg.text[1:]
            amount = int(amount)
            if amount <= user.balance:
                user.balance -= amount
            else:
                user.balance = 0
        else:
            amount = msg.text
            amount = int(amount)
            user.balance = amount
        user.save()
        answered_msg = await msg.answer("♻️ _Изменение баланса_", parse_mode="Markdown")
        await profile_shower(user, answered_msg.message_id, bot, answered_msg.chat.id)
    except Exception:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="‹ Назад", callback_data=f"usershow_{user.user_id}"))
        await msg.answer(add_remove_balance_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.callback_query(F.data.startswith("user_purchase_"))
async def user_purchase(call: CallbackQuery):
    data = call.data.split("_")
    user = await sync_to_async(TelegramUser.objects.get)(user_id=data[2])
    products = await sync_to_async(list)(Product.objects.filter(bought_by=user))
    if not products:
        await call.message.answer("История покупок пуста.")
        return
    await show_products_page(call, products, page=0)


@router.callback_query(F.data == "sell_statistics")
async def sell_statistics(call: CallbackQuery):
    stats = await get_statistics()
    text = stat_text.format(**stats)
    await call.message.edit_text(text, reply_markup=admin_statistics, parse_mode="Markdown")


@router.callback_query(F.data == "stat_products")
async def stat_products(call: CallbackQuery):
    # Загружаем данные из базы с обработкой `None`
    products = Product.objects.annotate(
        city_name=Coalesce('city__city_name', Value('Не указано'), output_field=CharField()),
        chapter_name=Coalesce('gram__chapter__chapter_name', Value('Не указано'), output_field=CharField()),
        rayon_name=Coalesce('rayon__rayon_name', Value('Не указано'), output_field=CharField()),
        bought_by_username=Coalesce('bought_by__username', Value('Не указано'), output_field=CharField()),
        gram_price=Coalesce('gram__price', Value('Не указано'), output_field=CharField())
    ).values(
        'city_name', 'rayon_name', 'bought_by_username', 'gram_price',
        'date_add', 'date_bought', 'address', 'reserved', 'chapter_name'
    )

    if not products.exists():
        await call.message.answer("Нет данных для экспорта.")
        return

    df = pd.DataFrame(list(products))

    if 'date_add' in df.columns:
        df['date_add'] = pd.to_datetime(df['date_add']).dt.tz_localize(None)
    if 'date_bought' in df.columns:
        df['date_bought'] = pd.to_datetime(df['date_bought']).dt.tz_localize(None)

    df.rename(columns={
        'city_name': 'Город',
        'rayon_name': 'Район',
        'chapter_name': 'Продукт',
        'bought_by_username': 'Куплен (username)',
        'gram_price': 'Цена',
        'date_add': 'Дата добавления',
        'date_bought': 'Дата покупки',
        'address': 'Адрес',
        'reserved': 'Зарезервировано'
    }, inplace=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Products"

    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width

    file_path = "products.xlsx"
    async with aiofiles.open(file_path, "wb") as file:
        wb.save(file_path)

    excel_file = FSInputFile(file_path)
    await call.message.answer_document(excel_file)


@router.callback_query(F.data == "stats_withdraw")
async def stat_invoices(call: CallbackQuery):
    # Загружаем данные из базы с обработкой `None`
    invoices = Invoice.objects.filter(complete=True).annotate(
        user_name=Coalesce('user__username', Value('Не указано'), output_field=CharField()),
        user_user_id=Coalesce('user__user_id', Value('Не указано'), output_field=CharField()),
        user_first_name=Coalesce('user__first_name', Value('Не указано'), output_field=CharField()),
    ).order_by('-created_at').values(
        'user_name', 'user_user_id', 'user_first_name',
        'kzt_amount', 'crypto_amount',
        'unique_pod', 'created_at', 'withdrawed_to_shop', 'txid_withdrawed_to_shop'
    )

    if not invoices.exists():
        await call.message.answer("Нет данных для экспорта.")
        return

    # Преобразуем в DataFrame
    df = pd.DataFrame(list(invoices))

    # Приводим datetime-поля к неосведомленным
    if 'created_at' in df.columns:
        df['created_at'] = df['created_at'].apply(
            lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else 'Не указано'
        )

    df.rename(columns={
        'user_name': 'Пользователь',
        'user_first_name': 'Имя пользователя',
        'user_id': "ID Пользователя",
        'kzt_amount': 'Сумма в KZT',
        'crypto_amount': 'Сумма в USDT',
        'unique_pod': 'Уникальный POD',
        'created_at': 'Дата создания',
        'withdrawed_to_shop': 'Выведено в магазин',
        'txid_withdrawed_to_shop': 'TXID вывода в магазин'
    }, inplace=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Invoices"

    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter  # Get the column name
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width

    file_path = "invoices.xlsx"
    async with aiofiles.open(file_path, "wb") as file:
        wb.save(file_path)

    excel_file = FSInputFile(file_path)
    await call.message.answer_document(excel_file)


class AddChapterState(StatesGroup):
    awaiting_title = State()
    awaiting_description = State()
    awaiting_photo = State()


@router.callback_query(F.data == "add_chapter")
async def add_chapter(call: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Отменить", callback_data="manage_products"))
    await state.set_state(AddChapterState.awaiting_title)
    await call.message.edit_text(add_chapter_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.message(AddChapterState.awaiting_title)
async def awaiting_chapter_title(msg: Message, state: FSMContext):
    new_chapter = await sync_to_async(Chapter.objects.create)(chapter_name=msg.text)
    escape = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text=">> Пропустить описание")]])
    await state.update_data(chapter_id=new_chapter.id)
    await state.set_state(AddChapterState.awaiting_description)
    await msg.answer("Введите описание раздела продуктов:", reply_markup=escape)


@router.message(AddChapterState.awaiting_description)
async def awaiting_chapter_description(msg: Message, state: FSMContext):
    escape = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text=">> Пропустить фото")]])
    if msg.text == ">> Пропустить описание":
        await msg.answer("Отправьте фото раздела продуктов:", reply_markup=escape)
        await state.set_state(AddChapterState.awaiting_photo)
        return
    data = await state.get_data()
    chapter_id = data.get("chapter_id")
    chapter = await sync_to_async(Chapter.objects.get)(id=chapter_id)
    chapter.description = msg.text
    chapter.save()
    await msg.answer("Отправьте фото раздела продуктов:", reply_markup=escape)
    await state.set_state(AddChapterState.awaiting_photo)


@router.message(AddChapterState.awaiting_photo)
async def awaiting_chapter_photo(msg: Message, state: FSMContext, bot: Bot):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    data = await state.get_data()
    chapter_id = data.get("chapter_id")
    chapter = await sync_to_async(Chapter.objects.get)(id=chapter_id)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="manage_products"))
    kb_deleter = await msg.answer("♻️ _Создание раздела_", reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")
    await asyncio.sleep(1)
    await kb_deleter.delete()
    try:
        if msg.text == ">> Пропустить фото":
            await msg.answer(f"✔️ _Новый раздел {escape_md(chapter.chapter_name)} создан_",
                             reply_markup=builder.as_markup(), parse_mode="MarkdownV2")
            await show_desc_or_photo(user, chapter, bot)
            await state.clear()
            return
        elif msg.photo:
            await msg.answer(f"✔️ _Новый раздел {escape_md(chapter.chapter_name)} создан_",
                             reply_markup=builder.as_markup(), parse_mode="MarkdownV2")
            photo = msg.photo[-1]
            file_id = photo.file_id
            chapter.photo = file_id
            chapter.save()
            await show_desc_or_photo(user, chapter, bot)
            await state.clear()
    except Exception as e:
        print(e)


class AddCityGeoState(StatesGroup):
    awaiting_city_name = State()
    choose_city_name = State()
    awaiting_rayon_name = State()


@router.callback_query(F.data == "add_city")
async def add_city(call: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Отменить", callback_data="manage_products"))
    await state.set_state(AddCityGeoState.awaiting_city_name)
    await call.message.edit_text(add_city_text, reply_markup=builder.as_markup(), parse_mode="Markdown")


@router.message(AddCityGeoState.awaiting_city_name)
async def awaiting_city_name(msg: Message, state: FSMContext):
    new_city = await sync_to_async(City.objects.create)(city_name=msg.text)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="manage_products"))
    await msg.answer(f" _Новый город {escape_md(new_city.city_name)} добавлен_", reply_markup=builder.as_markup(),
                     parse_mode="MarkdownV2")
    await state.clear()


@router.callback_query(F.data == "add_geo")
async def add_geo(call: CallbackQuery, state: FSMContext):
    cities = await sync_to_async(City.objects.all)()
    if cities:
        keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=city.city_name)] for city in cities], resize_keyboard=True)
        keyboard.keyboard.append([KeyboardButton(text="❌ Отменить")])
        await call.message.answer("Выберите из списка к какому городу хотите добавить район:", reply_markup=keyboard)
        await state.set_state(AddCityGeoState.choose_city_name)
    else:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🌆 Добавить Город", callback_data="add_city"))
        await call.message.answer("Для начала добавьте город.", reply_markup=builder.as_markup())

@router.message(AddCityGeoState.choose_city_name)
async def choose_city_name(msg: Message, state: FSMContext):
    try:
        if msg.text == "❌ Отменить":
            kb_deleter = await msg.answer("♻️ _Отмена добавления_", reply_markup=ReplyKeyboardRemove(),
                                          parse_mode="Markdown")
            await kb_deleter.delete()
            await msg.answer("Manage Products", reply_markup=admin_manage_products)
            await state.clear()
            return
        city = await sync_to_async(City.objects.get)(city_name=msg.text)
        if city:
            await state.update_data(city_id=city.id)
            await msg.answer("Введите название района:", reply_markup=ReplyKeyboardRemove())
            await state.set_state(AddCityGeoState.awaiting_rayon_name)
    except Exception as e:
        print(e)

@router.message(AddCityGeoState.awaiting_rayon_name)
async def awaiting_rayon_name(msg: Message, state: FSMContext):
    data = await state.get_data()
    city_id = data.get("city_id")
    city = await sync_to_async(City.objects.get)(id=city_id)
    new_rayon = await sync_to_async(Rayon.objects.create)(city=city, rayon_name=msg.text)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="manage_products"))
    await msg.answer(f" _Новый район {escape_md(new_rayon.rayon_name)} добавлен_", reply_markup=builder.as_markup(),
                     parse_mode="MarkdownV2")
    await state.clear()

class AddGramPriceState(StatesGroup):
    choose_chapter_name = State()
    awaiting_gram = State()
    awaiting_price = State()

@router.callback_query(F.data == "add_gram")
async def add_gram(call: CallbackQuery, state: FSMContext):
    chapters = await sync_to_async(Chapter.objects.all)()
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=chapter.chapter_name)] for chapter in chapters],
                                   resize_keyboard=True)
    keyboard.keyboard.append([KeyboardButton(text="❌ Отменить")])
    await state.set_state(AddGramPriceState.choose_chapter_name)
    await call.message.answer("Выберите из списка к какому разделу добавить фасовку:", reply_markup=keyboard)

@router.message(AddGramPriceState.choose_chapter_name)
async def choose_chapter_name(msg: Message, state: FSMContext):
    try:
        if msg.text == "❌ Отменить":
            kb_deleter = await msg.answer("♻️ _Отмена добавления_", reply_markup=ReplyKeyboardRemove(),
                                          parse_mode="Markdown")
            await kb_deleter.delete()
            await msg.answer("Manage Products", reply_markup=admin_manage_products)
            await state.clear()
            return
        chapter = await sync_to_async(Chapter.objects.get)(chapter_name=msg.text)
        if chapter:
            await state.update_data(chapter_id=chapter.id)
            await msg.answer("Введите фасовку, можно использовать дробные числа (`1.5`), так и целые числа (`1`, `2`):",
                             reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")
            await state.set_state(AddGramPriceState.awaiting_gram)
    except Exception as e:
        print(e)

@router.message(AddGramPriceState.awaiting_gram)
async def awaiting_gram(msg: Message, state: FSMContext):
    try:
        gram = float(msg.text.replace(',', '.'))
        await state.update_data(gram=gram)
        await msg.answer(f"Введите стоимость за {gram}г в *₸*:", reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")
        await state.set_state(AddGramPriceState.awaiting_price)
    except Exception as e:
        print(e)


@router.message(AddGramPriceState.awaiting_price)
async def awaiting_price(msg: Message, state: FSMContext):
    try:
        price = msg.text.replace('.', '').replace(',', '').replace(' ', '')
        data = await state.get_data()
        chapter_id = data.get("chapter_id")
        gram = data.get("gram")
        chapter = await sync_to_async(Chapter.objects.get)(id=chapter_id)
        new_gram = await sync_to_async(GramPrice.objects.create)(chapter=chapter, gram=float(gram), price=price)
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="manage_products"))
        await msg.answer(f"Фасовка `{new_gram.gram}`г \- {new_gram.price} *₸* добавлен к разделу {escape_md(chapter.chapter_name)}",
                         reply_markup=builder.as_markup(), parse_mode="MarkdownV2")
        await state.clear()
    except Exception as e:
        print(e)

class AddProductState(StatesGroup):
    awaiting_gram_price = State()
    choose_city_name = State()
    choose_rayon_name = State()
    adding_products = State()

@router.callback_query(F.data == "add_products")
async def add_products(call: CallbackQuery, state: FSMContext):
    gram_prices = await sync_to_async(GramPrice.objects.all)()
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=f"{i.chapter.chapter_name} {i.gram} {i.price}")] for i in gram_prices],
                                   resize_keyboard=True)
    keyboard.keyboard.append([KeyboardButton(text="❌ Отменить")])
    await state.set_state(AddProductState.awaiting_gram_price)
    await call.message.answer("Выберите из списка фасовку, к которой хотите добавить продукт:", reply_markup=keyboard)

@router.message(AddProductState.awaiting_gram_price)
async def awaiting_gram_price(msg: Message, state: FSMContext):
    try:
        if msg.text == "❌ Отменить":
            kb_deleter = await msg.answer("♻️ _Отмена добавления_", reply_markup=ReplyKeyboardRemove(),
                                          parse_mode="Markdown")
            await kb_deleter.delete()
            await msg.answer("Manage Products", reply_markup=admin_manage_products)
            await state.clear()
            return
        parts = msg.text.rsplit(" ", 2)
        chapter_name, gram, price = parts
        gram_price = await sync_to_async(GramPrice.objects.get)(chapter__chapter_name=chapter_name, gram=gram, price=int(price))
        cities = await sync_to_async(City.objects.all)()
        keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=city.city_name)] for city in cities],
                                       resize_keyboard=True)
        keyboard.keyboard.append([KeyboardButton(text="❌ Отменить")])
        await state.update_data(gram_price_id=gram_price.id)
        await state.set_state(AddProductState.choose_city_name)
        await msg.answer("Выберите из списка город, в котором будет доступен продукт:", reply_markup=keyboard)
    except Exception as e:
        print(e)


@router.message(AddProductState.choose_city_name)
async def product_choose_city(msg: Message, state: FSMContext):
    try:
        if msg.text == "❌ Отменить":
            kb_deleter = await msg.answer("♻️ _Отмена добавления_", reply_markup=ReplyKeyboardRemove(),
                                          parse_mode="Markdown")
            await kb_deleter.delete()
            await msg.answer("Manage Products", reply_markup=admin_manage_products)
            await state.clear()
            return
        city = await sync_to_async(City.objects.get)(city_name=msg.text)
        await state.update_data(city_id=city.id)
        rayons = await sync_to_async(Rayon.objects.filter)(city=city)
        keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=rayon.rayon_name)] for rayon in rayons],
                                       resize_keyboard=True)
        keyboard.keyboard.append([KeyboardButton(text="❌ Отменить")])
        await msg.answer("Выберите из списка район, в котором будет доступен продукт:", reply_markup=keyboard)
        await state.set_state(AddProductState.choose_rayon_name)
    except Exception as e:
        print(e)

@router.message(AddProductState.choose_rayon_name)
async def product_rayon_name(msg: Message, state: FSMContext):
    try:
        if msg.text == "❌ Отменить":
            kb_deleter = await msg.answer("♻️ _Отмена добавления_", reply_markup=ReplyKeyboardRemove(),
                                          parse_mode="Markdown")
            await kb_deleter.delete()
            await msg.answer("Manage Products", reply_markup=admin_manage_products)
            await state.clear()
            return
        rayon = await sync_to_async(Rayon.objects.get)(rayon_name=msg.text)
        await state.update_data(rayon_id=rayon.id)
        await state.set_state(AddProductState.adding_products)
        await msg.answer("Начните добавление, каждая новая строчка - это новый продукт:", reply_markup=ReplyKeyboardRemove())

    except Exception as e:
        print(e)

@router.message(AddProductState.adding_products)
async def adding_products(msg: Message, state: FSMContext):
    try:
        if msg.text == "❌ Отменить":
            kb_deleter = await msg.answer("♻️ _Отмена добавления_", reply_markup=ReplyKeyboardRemove(),
                                          parse_mode="Markdown")
            await kb_deleter.delete()
            await msg.answer("Manage Products", reply_markup=admin_manage_products)
            await state.clear()
            return
        data = await state.get_data()
        gram_price_id = data.get("gram_price_id")
        city_id = data.get("city_id")
        rayon_id = data.get("rayon_id")
        addresses = msg.text.strip().split("\n")
        products = [Product(city_id=city_id, rayon_id=rayon_id, gram_id=gram_price_id, address=address.strip())
                    for address in addresses if address.strip()]
        await sync_to_async(Product.objects.bulk_create)(products)
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="manage_products"))
        await msg.answer(f"✅ Добавлено {len(products)} продуктов.", reply_markup=builder.as_markup())
        await state.clear()
    except Exception as e:
        print(e)

class ConfPercentState(StatesGroup):
    awaiting_percent = State()

@router.callback_query(F.data == "conf_shop")
async def configurations(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(shop_configuration_text, reply_markup=conf_kb, parse_mode="Markdown")

@router.callback_query(F.data == "change_ref_percent")
async def change_ref_percent(call: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Отменить", callback_data="conf_shop"))
    await state.set_state(ConfPercentState.awaiting_percent)
    await call.message.edit_text(change_ref_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.message(ConfPercentState.awaiting_percent)
async def awaiting_percent(msg: Message, state: FSMContext):
    try:
        prc = float(msg.text.replace(',', '.'))
        conf = await sync_to_async(ShopConfiguration.objects.filter)()
        if not conf:
            conf = await sync_to_async(ShopConfiguration.objects.create)(ref_percent=2)
        conf.ref_percent = prc
        conf.save()
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="conf_shop"))
        await msg.answer(f"✅ Процент по реферальной системе изменен на {prc}%")
        await state.clear()
    except Exception as e:
        print(e)


@router.callback_query(F.data == "shop_balance")
async def shop_balance(call: CallbackQuery):
    try:
        total_balance = await sync_to_async(
            lambda: Invoice.objects.filter(complete=True, withdrawed_to_shop=False)
            .aggregate(Sum("kzt_amount"), invoice_count=Count("id")))()
        balance = total_balance["kzt_amount__sum"] or 0
        builder = InlineKeyboardBuilder()
        if balance > 0:
            balance_coms = balance / 100 * 90

            builder.add(InlineKeyboardButton(text="Запросить вывод", callback_data="vivod_please"))
            builder.add(InlineKeyboardButton(text="Все инвойсы", callback_data="all_invoices"))
            builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="back_to_admin_menu"))
            builder.adjust(1)

            text = f"💰 *Баланс магазина:* {balance_coms} *₸*\n\n❕ _Сумма указана с учетом нашей комиссии_"
            withdraw_requests = await sync_to_async(
                lambda: WithdrawInvoices.objects.filter(complete=False)
            )()

            if withdraw_requests:
                total_kzt_amount = await sync_to_async(
                    lambda: withdraw_requests.aggregate(Sum('invoices_to_withdraw__kzt_amount'))
                )()

                total_kzt = total_kzt_amount['invoices_to_withdraw__kzt_amount__sum'] or 0
                if total_kzt > 10000:
                    total_kzt = total_kzt / 100 * 90
                    text += f"\n\n♻️ _На стадии вывода_: {total_kzt}"
            await call.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
        else:
            builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="back_to_admin_menu"))
            text = f"💰 *Баланс магазина:* {balance} *₸*"
            await call.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())

    except Exception as e:
        print(e)
        await call.message.answer("⚠️ Произошла ошибка при получении баланса.")

@router.callback_query(F.data == "all_invoices")
async def all_invoices(call: CallbackQuery):
    invoices = await sync_to_async(list)(Invoice.objects.filter(complete=True, withdrawed_to_shop=False))
    if invoices:
        total_pages = (len(invoices) + PAGE_SIZE - 1) // PAGE_SIZE
        page_number = 1

        @router.callback_query(F.data.startswith("next_inv_page_"))
        async def next_inv_page(call: CallbackQuery):
            nonlocal page_number
            page_number += 1
            if page_number > total_pages:
                page_number = total_pages
            await send_invoices_page(call, page_number, total_pages, invoices)

        @router.callback_query(F.data.startswith("prev_inv_page_"))
        async def prev_inv_page(call: CallbackQuery):
            nonlocal page_number
            page_number -= 1
            if page_number < 1:
                page_number = 1
            await send_invoices_page(call, page_number, total_pages, invoices)

        async def send_invoices_page(call: CallbackQuery, page_number: int, total_pages: int, invoices):
            start_index = (page_number - 1) * PAGE_SIZE
            end_index = min(start_index + PAGE_SIZE, len(invoices))
            invoices_page = invoices[start_index:end_index]

            builder = InlineKeyboardBuilder()
            for invoice in invoices_page:
                builder.row(InlineKeyboardButton(
                    text=f"💰 {invoice.kzt_amount} ₸ | {invoice.user.username if invoice.user.username else invoice.user.first_name}",
                    callback_data=f"invoice_{invoice.id}"))
            builder.adjust(2)
            if page_number > 1:builder.row(InlineKeyboardButton(text="◀️ Предыдущая страница", callback_data=f"prev_inv_page_{page_number - 1}"))
            if page_number < total_pages:
                builder.row(InlineKeyboardButton(text="Следующая страница ▶️", callback_data=f"next_inv_page_{page_number + 1}"))

            builder.row(InlineKeyboardButton(text="‹ Назад", callback_data="shop_balance"))
            await call.message.edit_text("📑 *Список ожидающих инвойсов*",
                                         reply_markup=builder.as_markup(),
                                         parse_mode="Markdown")
        await send_invoices_page(call, page_number, total_pages, invoices)
    else:
        await call.message.answer("👀 _Нет ожидающих инвойсов_", parse_mode="Markdown")

@router.callback_query(F.data.startswith("invoice_"))
async def show_invoice(call: CallbackQuery):
    try:
        invoice_id = int(call.data.split("_")[1])
        invoice = await sync_to_async(Invoice.objects.get)(id=invoice_id)
        user_info = f"👤 Пользователь: {escape_markdown_v2(invoice.user.username) if invoice.user.username else str(invoice.user.user_id)}"
        method = f"💳 Метод оплаты: {escape_markdown_v2(invoice.method) if invoice.method else 'Не указан'}"
        amount_kzt = f"🇰🇿 Сумма ₸: {invoice.kzt_amount}"
        amount_crypto = f"🪙 Крипто сумма: {escape_markdown_v2(str(invoice.crypto_amount) if invoice.crypto_amount else 'Не указана')}"
        status = "✅ Завершён" if invoice.complete else "❌ Не завершён"
        withdrawn_status = "💸 Выведен в магазин" if invoice.withdrawed_to_shop else "⏳ Ожидает вывода"
        created_at = f"🕒 Дата создания: {escape_markdown_v2(invoice.created_at.strftime('%d.%m.%Y %H:%M'))}"
        txid = f"🔗 TXID: {escape_markdown_v2(invoice.txid_withdrawed_to_shop) if invoice.txid_withdrawed_to_shop else 'Нет данных'}"

        text = "\n".join([user_info, method, amount_kzt, amount_crypto, status, withdrawn_status, created_at, txid])

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="‹ Назад", callback_data="all_invoices"))

        await call.message.edit_text(f"📄 *Детали инвойса* \\#{invoice.id}\n\n{text}",
                                     reply_markup=builder.as_markup(),
                                     parse_mode="MarkdownV2")
    except Exception as e:
        print(e)
        await call.message.answer("⚠️ Ошибка при получении информации об инвойсе.")

class WithdrawToShop(StatesGroup):
    awaiting_usdt = State()

@router.callback_query(F.data == "vivod_please")
async def vivod_please(call: CallbackQuery, bot: Bot):
    with_invoices = await sync_to_async(WithdrawInvoices.objects.filter)(complete=False)
    if not with_invoices:
        super_admin = await sync_to_async(TelegramUser.objects.filter)(is_super_admin=True)
        invoices_to_withdraw = await sync_to_async(Invoice.objects.filter)(complete=True, withdrawed_to_shop=False)
        user = await sync_to_async(TelegramUser.objects.get)(user_id=call.from_user.id)
        conf = await sync_to_async(ShopConfiguration.objects.first)()
        new_invoice_request = await sync_to_async(WithdrawInvoices.objects.create)()
        total_balance = await sync_to_async(
            Invoice.objects.filter(complete=True, withdrawed_to_shop=False).aggregate
        )(Sum("kzt_amount"), invoice_count=Count("id"))
        balance = total_balance["kzt_amount__sum"] or 0
        if balance > 10000:
            balance_coms = balance / 100 * 90
            for invoice in invoices_to_withdraw:
                await sync_to_async(new_invoice_request.invoices_to_withdraw.add)(invoice)
            builder = InlineKeyboardBuilder()
            text = (f"Отправить: {balance_coms}\n"
                    f"Без комсы: {balance}\n"
                    f"Кошелек: `{conf.USDT_TRC20}`")
            builder.add(InlineKeyboardButton(text="Выведен", callback_data=f"super_admin_withdraw_{new_invoice_request.id}_{user.user_id}"))
            for super_admin in super_admin:
                await bot.send_message(chat_id=super_admin.user_id, text=text, reply_markup=builder.as_markup(), parse_mode="Markdown")
            await call.message.answer(f"✔️ Вывод на сумму {balance} запрошен!")
    else:
        await call.message.answer("💫 _Вывод сейчас невозможен, ожидайте вывода прошлой заявки_")

class USDTAddress(StatesGroup):
    awaiting_trc20 = State()

@router.callback_query(F.data == "type_usdt_trc20")
async def type_usdt_trc20(call: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Отменить", callback_data="conf_shop"))
    await state.set_state(USDTAddress.awaiting_trc20)
    await call.message.edit_text(usdt_trc20_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.message(USDTAddress.awaiting_trc20)
async def awaiting_usdt_address(msg: Message, state: FSMContext):
    conf = await sync_to_async(ShopConfiguration.objects.first)()
    conf.USDT_TRC20 = msg.text
    conf.save()
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="‹ Настройки", callback_data="conf_shop"))
    await msg.answer(f"✔️ _Ваш кошелек изменен_:\n"
                     f"`{conf.USDT_TRC20}`", reply_markup=builder.as_markup(), parse_mode="Markdown")
