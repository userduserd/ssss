import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
from tg.models import UserBot
import asyncio
import logging
from aiogram import Bot, Dispatcher
from tg.handlers import start, magazine, exchange, add_balance, personal_bot, admin, user_history, promo, refs, report, super_admin
from aiogram.filters import BaseFilter
from aiogram.types import Message
from tg.models import TelegramUser
from tg.handlers.utils import periodic_bot_checker
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

print(TELEGRAM_BOT_TOKEN)


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


async def main():
    from aiogram.enums.parse_mode import ParseMode
    from aiogram.fsm.storage.memory import MemoryStorage

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_routers(exchange.router, start.router, magazine.router, add_balance.router, personal_bot.router,
                       admin.router, user_history.router, promo.router, refs.router, report.router, super_admin.router)
    dp.message.filter(IsNotBannedFilter())
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(periodic_bot_checker())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())