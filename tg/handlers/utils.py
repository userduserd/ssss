import signal
import subprocess
from aiohttp import ClientConnectorError
import aiohttp
from aiogram.fsm.state import StatesGroup, State
import asyncio
from aiogram.types import InlineKeyboardButton, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
from tg.models import Invoice, Product, City, Rayon, Chapter, GramPrice, TelegramUser, UserBot, PromoCode
from aiogram import Bot as MBot
from .text import broadcasting_text, profile_text
import os
import re
from django.db.models import Sum
from datetime import  timedelta
from django.utils import timezone
from dotenv import load_dotenv
load_dotenv()

class CheckState(StatesGroup):
    awaiting_check = State()


def escape_md(text: str) -> str:
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

def escape_markdown_v2(text: str) -> str:
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!', '\n']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


async def vitrina_text():
    text = ""
    cities = await sync_to_async(City.objects.all)()
    for city in cities:
        text += f"═══🇰🇿 *{city.city_name.upper()}* 🇰🇿═══\n"
        chapters = await sync_to_async(Chapter.objects.all)()
        for chapter in chapters:
            text += f"════*{chapter.chapter_name.upper()}*\n"
            grams = await sync_to_async(GramPrice.objects.filter)(chapter=chapter)
            for gram in grams:
                text += f"══════*Вес {gram.gram}г*\n"
                rayons = await sync_to_async(Rayon.objects.filter)(city=city)
                for rayon in rayons:
                    product = await sync_to_async(Product.objects.filter)(rayon=rayon, city=city, gram=gram, bought_by=None)
                    if product:
                        text += f"      ✅{rayon.rayon_name.upper()}=*{gram.price} ₸* ({len(product)}шт)\n"
            text += "\n"
    return text


async def rassilksa(msg, text, Bot):
    users = await sync_to_async(TelegramUser.objects.all)()
    user_bots = await sync_to_async(UserBot.objects.filter)(is_active=True)
    count = 0
    amount = 0
    b_amount = 0
    p_amount = 0
    p_b_amount = 0
    for i in users:
        try:
            await Bot.send_message(chat_id=i.user_id, text=text)
            amount += 1
        except Exception:
            b_amount += 1
        count += 1
        if count >= 10:
            await Bot.edit_message_text(text=broadcasting_text.format(amount=amount, b_amount=b_amount, p_amount=p_amount,
                                                                      p_b_amount=p_b_amount), message_id=msg.message_id)
        await asyncio.sleep(3)
    for i in user_bots:
        n_bot = Bot(token=i.bot_token)
        try:
            await n_bot.send_message(chat_id=i.user.user_id, text=text)
            p_amount += 1
        except Exception:
            p_b_amount += 1
        await asyncio.sleep(3)


async def rassilka(msg, text, Bot):
    users = await sync_to_async(list)(TelegramUser.objects.filter(is_admin=False))
    user_bots = await sync_to_async(list)(UserBot.objects.filter(is_active=True))
    count = 0
    amount = 0
    b_amount = 0
    p_amount = 0
    p_b_amount = 0
    for i in users:
        try:
            await Bot.send_message(chat_id=i.user_id, text=text)
            amount += 1
        except Exception:
            b_amount += 1
        count += 1
        if count % 10 == 0:
            await Bot.edit_message_text(
                text=broadcasting_text.format(amount=amount, b_amount=b_amount, p_amount=p_amount, p_b_amount=p_b_amount),
                chat_id=msg.chat.id, message_id=msg.message_id, parse_mode="Markdown")
        await asyncio.sleep(3)

    for i in user_bots:
        async with MBot(token=i.bot_token) as n_bot:
            try:
                await n_bot.send_message(chat_id=i.user.user_id, text=text)
                p_amount += 1
            except Exception:
                p_b_amount += 1
            count += 1
            if count % 10 == 0:
                await Bot.edit_message_text(
                    text=broadcasting_text.format(amount=amount, b_amount=b_amount, p_amount=p_amount, p_b_amount=p_b_amount),
                    chat_id=msg.chat.id, message_id=msg.message_id, parse_mode="Markdown")
            await asyncio.sleep(3)
    text = broadcasting_text.format(amount=amount, b_amount=b_amount, p_amount=p_amount, p_b_amount=p_b_amount)
    text += "✅ *Рассылка завершена!*"
    await Bot.edit_message_text(chat_id=msg.chat.id, text=text, message_id=msg.message_id, parse_mode="Markdown")


async def check_bot(bot_token):
    try:
        bot = MBot(token=bot_token)
        await bot.get_me()
        return True
    except Exception as e:
        return False
    finally:
        await bot.session.close()


async def terminate_process(pid):
    pid = int(pid)
    try:
        os.kill(pid, signal.SIGKILL)
        user_bot = await sync_to_async(UserBot.objects.get)(pid=pid)
        user_bot.is_active = False
        user_bot.save()
        print(f"Пытаюсь завершить процесс с PID {pid}")
    except Exception as e:
        print(e)


def kill_process(pid):
    try:
        pid = int(pid)
        result = subprocess.run(['kill', '-9', str(pid)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode == 0:
            print(f"Процесс с PID {pid} успешно завершен.")
        else:
            print(f"Ошибка при завершении процесса с PID {pid}.")
            print(f"Ошибка: {result.stderr.decode()}")

    except Exception as e:
        print(f"Произошла ошибка: {e}")


async def periodic_bot_checker():
    while True:
        user_bots = await sync_to_async(UserBot.objects.filter)(is_active=True)
        for user_bot in user_bots:
            check = await check_bot(user_bot.bot_token)
            if not check:
                await terminate_process(user_bot.pid)
                user_bot.is_active = False
                user_bot.save()
        await asyncio.sleep(10)


async def get_total_purchases(user):
    try:
        return await sync_to_async(
            lambda: Product.objects.filter(bought_by=user).count()
        )()
    except Exception as e:
        print("GET TOTAL POK", e)
        return 0

async def get_total_invoices(user):
    try:
        return await sync_to_async(
            lambda: Invoice.objects.filter(user=user, complete=True).count()
        )()
    except Exception as e:
        print("GET TOTAL INV", e)
        return 0

async def get_total_promo(user):
    try:
        return await sync_to_async(lambda: PromoCode.objects.filter(user=user).count())()
    except Exception as e:
        print("GET TOTAL PROMO", e)
        return 0

async def get_total_promo_amount(user):
    try:
        return await sync_to_async(
            lambda: PromoCode.objects.filter(user=user, active=False).aggregate(total_amount=Sum('amount'))['total_amount'] or 0)()
    except Exception as e:
        print("GET TOTAL PROMO AMOUNT", e)
        return 0

async def namer(user):
    if user.username:
        return f"@{user.username}"

    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    return escape_md(full_name)


async def profile_shower(user, edit_msg_id, bot, chat_id):
    await asyncio.sleep(1)
    amount_pok = await get_total_purchases(user)
    amount_pop = await get_total_invoices(user)
    amount_promo = await get_total_promo(user)
    sum_amount_promo = await get_total_promo_amount(user)
    referred_by = "Никто"
    if user.referred_by:
        referred_by = await namer(user.referred_by)
    text = profile_text.format(user_id=user.user_id, balance=user.balance, amount_pok=amount_pok, amount_pop=amount_pop,
                               date_reg=user.created_at.strftime('%Y-%m-%d %H:%M:%S'), amount_promo=amount_promo,
                               sum_amount_promo=sum_amount_promo, ref_code=user.referral_code, ref_user=referred_by)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🛒 Покупки", callback_data=f"user_purchase_{user.user_id}"))
    builder.add(InlineKeyboardButton(text="➕➖ Баланс", callback_data=f"user_balance_{user.user_id}"))
    builder.add(InlineKeyboardButton(text=f"{'🟢' if user.is_admin else '🔴'} Администратор",
                                     callback_data=f"add_delete_admin_{user.user_id}"))
    builder.add(InlineKeyboardButton(text=f"{'❌ Заблокировать' if not user.is_banned else '✅ Разблокировать'}",
                                     callback_data=f"ban_unban_{user.user_id}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="‹ Назад", callback_data=f"manage_users"))
    await bot.edit_message_text(chat_id=chat_id, text=text, message_id=edit_msg_id, reply_markup=builder.as_markup(), parse_mode="Markdown")

async def profile_edited_shower(user, call):
    amount_pok = await get_total_purchases(user)
    amount_pop = await get_total_invoices(user)
    amount_promo = await get_total_promo(user)
    sum_amount_promo = await get_total_promo_amount(user)
    referred_by = "Никто"
    if user.referred_by:
        referred_by = await namer(user.referred_by)
    text = profile_text.format(user_id=user.user_id, balance=user.balance, amount_pok=amount_pok, amount_pop=amount_pop,
                               date_reg=user.created_at.strftime('%Y-%m-%d %H:%M:%S'), amount_promo=amount_promo,
                               sum_amount_promo=sum_amount_promo, ref_code=user.referral_code, ref_user=referred_by)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🛒 Покупки", callback_data=f"user_purchase_{user.user_id}"))
    builder.add(InlineKeyboardButton(text="➕➖ Баланс", callback_data=f"user_balance_{user.user_id}"))
    builder.add(InlineKeyboardButton(text=f"{'🟢' if user.is_admin else '🔴'} Администратор",
                                     callback_data=f"add_delete_admin_{user.user_id}"))
    builder.add(InlineKeyboardButton(text=f"{'❌ Заблокировать' if not user.is_banned else '✅ Разблокировать'}",
                                     callback_data=f"ban_unban_{user.user_id}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="‹ Назад", callback_data=f"manage_users"))
    await call.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")


async def create_usdt_invoice(amount):
    account = os.getenv("APIRONE_ACC")
    create_invoice_url = f'https://apirone.com/api/v2/accounts/{account}/invoices'
    course = await get_course_retry()
    if course is not None:
        usdt_price = float(amount) / float(course)
        decimal_places = 6
        amount_in_microunits = int(usdt_price * 10 ** decimal_places)
        invoice_data = {
            "amount": amount_in_microunits,
            "currency": "usdt@trx",
            "lifetime": 2000,
            "callback_url": "http://example.com",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    create_invoice_url,
                    json=invoice_data,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    invoice_info = await response.json()
            print("INVOICE INFO", invoice_info)
            return invoice_info, usdt_price
        except ClientConnectorError as e:
            await create_usdt_invoice(amount)


async def get_course_retry(max_retries=10):
    url = os.getenv("COURSE_URL")

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        json_data = await response.json()
            return json_data.get('course')
        except aiohttp.ClientConnectorError as e:
            await asyncio.sleep(1)
    return None


async def get_req(kzt_amount, bot):
    url = os.getenv("REQ_URL")
    url = "http://38.244.134.231:8000/req/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"amount": kzt_amount,
                                               "bot": bot}) as res:
                if res.status == 200:
                    json_data = await res.json()
                    req = json_data.get("req")
                    uniq_invoice_id = json_data.get("invoice_id")
                    return req, uniq_invoice_id
    except Exception as e:
        print("Exception:", e)


async def check_invoice(invoice_id, msg, user, kzt_amount, db_invoice):
    while True:
        url = f"https://apirone.com/api/v2/invoices/{invoice_id}"
        db_invoice = await sync_to_async(Invoice.objects.get)(id=db_invoice.id)
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="‹ Главное меню", callback_data="back_to_menu"))
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as res:
                    if res.status == 200:
                        invoice_data = await res.json()
                        if not db_invoice.active:
                            break
                        for i in invoice_data['history']:
                            if i['status'] == 'partpaid':
                                course = await get_course_retry()
                                amount_usdt = float(i['amount']) / 1000000
                                amount_kzt = amount_usdt * float(course)
                                user.balance += int(amount_kzt)
                                user.save()
                                await msg.answer(f"➕ _Ваш баланс пополнен {int(amount_kzt)}_ *₸*", parse_mode="Markdown",
                                                 reply_markup=builder.as_markup())
                                db_invoice.kzt_amount = amount_kzt
                                db_invoice.crypto_amount = amount_usdt
                                db_invoice.active = False
                                db_invoice.complete = True
                                db_invoice.save()
                                break
                        if invoice_data['status'] == 'completed':
                            user.balance += kzt_amount
                            user.save()
                            await msg.answer(f"➕ _Ваш баланс пополнен {int(kzt_amount)}_ *₸*", parse_mode="Markdown",
                                             reply_markup=builder.as_markup())
                            db_invoice.active = False
                            db_invoice.complete = True
                            db_invoice.save()
                            break
                        if invoice_data['status'] == 'expired':
                            db_invoice.active = False
                            db_invoice.save()
                            await msg.answer("👀 _Вы просрочили время_", parse_mod="Markdown",
                                             reply_markup=builder.as_markup())
                            break
                    await asyncio.sleep(60)
        except Exception as e:
            print(e)

async def check_invoice_paid(msg, invoice, user):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="‹ Главное меню", callback_data="back_to_menu"))
    minutes = 0
    while True:
        try:
            if minutes >= 10:
                break
            url = os.getenv("CHECK_URL")
            invoice = await sync_to_async(Invoice.objects.get)(id=invoice.id)
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"uniq_id": invoice.unique_pod}) as res:
                    if res.status == 200:
                        json_data = await res.json()
                        status = json_data.get("status")
                        print("STATUS", status)
                        if status:
                            amount = json_data.get("amount")
                            user.balance += amount
                            user.save()
                            invoice.complete = True
                            invoice.active = False
                            invoice.save()
                            await msg.answer(f"➕ _Ваш баланс пополнен {int(invoice.kzt_amount)}_ *₸*", parse_mode="Markdown",
                                             reply_markup=builder.as_markup())
                            break
                    minutes += 1
                    await asyncio.sleep(60)
        except Exception as e:
            print(e)

async def get_statistics():
    now = timezone.now()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(weeks=1)
    month_ago = now - timedelta(days=30)

    con_24 = await sync_to_async(lambda: TelegramUser.objects.filter(created_at__gte=day_ago).count())()
    con_ned = await sync_to_async(lambda: TelegramUser.objects.filter(created_at__gte=week_ago).count())()
    con_mes = await sync_to_async(lambda: TelegramUser.objects.filter(created_at__gte=month_ago).count())()

    sell_24 = await sync_to_async(lambda: Product.objects.filter(date_bought__gte=day_ago).count())()
    sell_ned = await sync_to_async(lambda: Product.objects.filter(date_bought__gte=week_ago).count())()
    sell_mes = await sync_to_async(lambda: Product.objects.filter(date_bought__gte=month_ago).count())()

    pers_bots = await sync_to_async(lambda: UserBot.objects.filter(is_active=True).count())()

    pos = await sync_to_async(lambda: Invoice.objects.filter(complete=True).aggregate(total=Sum('kzt_amount'))['total'] or 0)()
    viv = await sync_to_async(lambda: Invoice.objects.filter(withdrawed_to_shop=True).aggregate(total=Sum('kzt_amount'))['total'] or 0)()

    return {
        "con_24": con_24,
        "con_ned": con_ned,
        "con_mes": con_mes,
        "sell_24": sell_24,
        "sell_ned": sell_ned,
        "sell_mes": sell_mes,
        "pers_bots": pers_bots,
        "pos": pos,
        "viv": viv,
    }

async def show_desc_or_photo(user, chapter, bot):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_msg_description"))
    if chapter.photo and chapter.description:

        await bot.send_photo(chat_id=user.user_id, photo=chapter.photo, caption=chapter.description, reply_markup=builder.as_markup())
    elif chapter.photo and not chapter.description:
        await bot.send_photo(chat_id=user.user_id, photo=chapter.photo, reply_markup=builder.as_markup())
    elif chapter.description and not chapter.photo:
        await bot.send_message(chat_id=user.user_id, text=chapter.description, reply_markup=builder.as_markup())


def parse_number(number_str: str) -> int:
    number_str = number_str.replace('.', '').replace(',', '').replace(' ', '')
    try:
        return int(number_str)
    except Exception as e:
        print(e)


async def chapter_texter(chapter):
    text = (f"📦 *{escape_markdown_v2(chapter.chapter_name)}* 📦\n\n"
            f"{f'🧩 * Описание:*{chapter.description}' if chapter.description else '🧩 *Описание отсутствует*'}")
    return text


async def changing_chapter_func(msg, chapter):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🖼 Фото", callback_data=f"photo_change_ch_{chapter.id}"))
    builder.add(InlineKeyboardButton(text="📃 Описание", callback_data=f"desc_change_ch_{chapter.id}"))
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="⚖️ Фасовка/Цены", callback_data=f"gramprice_change_ch_{chapter.id}"))
    builder.row(InlineKeyboardButton(text="‹ Назад", callback_data="change_chapter"))
    text = await chapter_texter(chapter)
    if chapter.photo:
        await msg.answer_photo(photo=chapter.photo, caption=text, reply_markup=builder.as_markup(), parse_mode="MarkdownV2")
    else:
        await msg.answer(text=text, reply_markup=builder.as_markup(), parse_mode="MarkdownV2")
