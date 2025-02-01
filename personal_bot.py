import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
from aiogram.exceptions import TelegramUnauthorizedError
import sys
import asyncio
import logging
from aiogram.filters import BaseFilter
from aiogram import Bot, Dispatcher
from tg.handlers import start, magazine, exchange, add_balance, personal_bot, admin, user_history, promo, refs, report, super_admin
from tg.models import UserBot, TelegramUser
from aiogram.fsm.storage.memory import MemoryStorage
from asgiref.sync import sync_to_async
from aiogram.types import Message

class IsNotBannedFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user_id = message.from_user.id
        try:
            user = TelegramUser.objects.get(user_id=user_id)
            if user.is_super_admin:
                return True
            return not user.is_banned
        except TelegramUser.DoesNotExist:
            return True

async def main(token: str):
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_routers(exchange.router, start.router, magazine.router, add_balance.router, personal_bot.router,
                       admin.router, user_history.router, promo.router, refs.router, report.router, super_admin.router)
    dp.message.filter(IsNotBannedFilter())
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except TelegramUnauthorizedError:
        user_bot = await sync_to_async(UserBot.objects.get)(bot_token=token)
        user_bot.is_active = False
        await sync_to_async(user_bot.save)()
    except Exception as e:
        print(e)
    finally:
        user_bot = await sync_to_async(UserBot.objects.get)(bot_token=token)
        user_bot.is_active = False
        await sync_to_async(user_bot.save)()
        await bot.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        raise ValueError("Token not provided!")
    asyncio.run(main(token))



