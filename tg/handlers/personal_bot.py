import asyncio
import logging
import os

import random
import subprocess

from aiogram import Router, Bot, F, Dispatcher
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from .text import personal_bot_add_text, personal_bot_text
from tg.models import TelegramUser, City, Rayon, Product, GramPrice, Invoice, Req, UserBot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
import sys
from aiogram.fsm.storage.memory import MemoryStorage

from .utils import escape_md

# sys.path.append('....')
# from mainkz import start_user_bots

router = Router()


class UserBotState(StatesGroup):
    awaiting_token = State()


@router.callback_query(F.data == "create_own_bot")
async def create_own_bot(call: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="back_to_menu"))
    await call.message.edit_text(personal_bot_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await state.set_state(UserBotState.awaiting_token)


@router.message(UserBotState.awaiting_token)
async def awaiting_token(msg: Message, state: FSMContext):
    user = await sync_to_async(TelegramUser.objects.get)(user_id=msg.from_user.id)
    user_bot = await sync_to_async(UserBot.objects.filter)(user=user, is_active=True)
    if user_bot:
        user_bot = user_bot.first()
        bot = Bot(user_bot.bot_token)
        escaped_bot_user = escape_md(user_bot.bot_name)
        try:
            bot = await bot.get_me()
            if bot:
                await msg.answer(personal_bot_add_text.format(bot_user=escaped_bot_user), parse_mode="Markdown")
        except Exception as e:
            user_bot.active = False
            user_bot.save()
            await msg.answer(f"Созданный ранее бот @{escaped_bot_user} не активен!\n\nОтправьте токен еще раз:", parse_mode="Markdown")
    else:
        token = msg.text.strip()
        try:
            bot = Bot(token)
            user_bot_info = await bot.get_me()
            bot_username = user_bot_info.username
            escaped_bot_user = bot_username.replace("_", "\\_")
            await msg.answer(personal_bot_add_text.format(bot_user=escaped_bot_user), parse_mode="Markdown")
            asyncio.create_task(runner(token, user, msg))
        except Exception as e:
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text="‹ Назад", callback_data="back_to_menu"))
            await msg.answer(personal_bot_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        finally:
            await bot.session.close()
            await state.clear()


async def runner(token, user, msg):
    venv_path = "/root/ssss/env/bin/python3"
    personal_bot_script = "/root/ssss/ssss/personal_bot.py"
    command = f'nohup {venv_path} {personal_bot_script} {token} > /dev/null 2>&1 &'
    bot = Bot(token)
    bot_info = await bot.get_me()
    try:
        user_bot, created = await sync_to_async(UserBot.objects.get_or_create)(user=user, is_active=True)
        process = subprocess.Popen(command, shell=True, preexec_fn=os.setpgrp)
        user_bot.bot_name = bot_info.username
        user_bot.bot_token = token
        user_bot.pid = process.pid + 1
        user_bot.save()
    except Exception as e:
        logging.error(f"Ошибка при запуске копии бота: {e}")

