from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

menu = [
    [InlineKeyboardButton(text="🛒 Магазин", callback_data="start_buy")],
    [InlineKeyboardButton(text="➕ Пополнить баланс", callback_data="add_balance")],
    [InlineKeyboardButton(text="🎁 Покупки", callback_data="user_history"),
     InlineKeyboardButton(text="🏷 Промокод", callback_data="add_promo")],
     [InlineKeyboardButton(text="👥 Рефералка", callback_data="ref"),
     InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/Versace_support_bot")],
    [InlineKeyboardButton(text="⚠️ Создать своего бота", callback_data="create_own_bot")],
    # [InlineKeyboardButton(text="⚡️Наши ресурсы", callback_data="resources")],
    # [InlineKeyboardButton(text="☎️ Поддержка", url="https://t.me/Gazgolder_support1")],
    # [InlineKeyboardButton(text="Бот сделан сервисом T-REX", url="https://t.me/")],
]
menu = InlineKeyboardMarkup(inline_keyboard=menu)




back_to_menu = [
    [InlineKeyboardButton(text="< Назад", callback_data="back_to_menu")]
]
back_to_menu = InlineKeyboardMarkup(inline_keyboard=back_to_menu)

menu_button = KeyboardButton(text="ℹ️ Показать меню")
menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[menu_button]])

admin = [
    [InlineKeyboardButton(text="💠 Витрина (в разработке)", callback_data="show_products")],
    [InlineKeyboardButton(text="🛍️ Продукты", callback_data="manage_products"),
     InlineKeyboardButton(text="⚙️ Настройки", callback_data="conf_shop")],
    [InlineKeyboardButton(text="📣 Рассылка", callback_data="send_msg_to_all"),
     InlineKeyboardButton(text="👥 Пользователи", callback_data="manage_users")],
    [InlineKeyboardButton(text="📊 Статистика", callback_data="sell_statistics"),
     InlineKeyboardButton(text="💳 Баланс магазина", callback_data="shop_balance")],
    [InlineKeyboardButton(text="🤖 Персональные боты", callback_data="personal_bots")]]


admin = InlineKeyboardMarkup(inline_keyboard=admin)

admin_statistics = [
    [InlineKeyboardButton(text="По продажам", callback_data="stat_products")],
    [InlineKeyboardButton(text="По вводам", callback_data="stats_withdraw")],
    [InlineKeyboardButton(text="‹ Назад", callback_data="back_to_admin_panel")]
]
admin_statistics = InlineKeyboardMarkup(inline_keyboard=admin_statistics)

admin_manage_users = [
    [InlineKeyboardButton(text="Найти пользователя", callback_data="find_profile")],

]

admin_manage_products = [
    [InlineKeyboardButton(text="➕ Добавить продукты ➕", callback_data="add_products")],
     [InlineKeyboardButton(text="📦 Новый раздел товаров", callback_data="add_chapter"),
      InlineKeyboardButton(text="⚖️ Добавить Фасовку", callback_data="add_gram")],
    [InlineKeyboardButton(text="🌆 Добавить Город", callback_data="add_city"),
     InlineKeyboardButton(text="🗺️ Добавить Район", callback_data="add_geo")],
    [InlineKeyboardButton(text="✍️ Редактировать", callback_data="change_customs")],
     [InlineKeyboardButton(text="‹ Назад", callback_data="back_to_admin_panel")]]

admin_manage_products = InlineKeyboardMarkup(inline_keyboard=admin_manage_products)

change_customs_kb = [
    [InlineKeyboardButton(text="✍️ Раздел", callback_data="change_chapter")],
    [InlineKeyboardButton(text="✍️ Город", callback_data="change_cities"),
     InlineKeyboardButton(text="✍️ Район", callback_data="change_geos")],
    [InlineKeyboardButton(text="‹ Назад", callback_data="manage_products")]]
change_customs_kb = InlineKeyboardMarkup(inline_keyboard=change_customs_kb)
admin_back_to_menu_kb = [
    [InlineKeyboardButton(text="‹ Назад", callback_data="back_to_admin_panel")]
]
admin_back_to_menu_kb = InlineKeyboardMarkup(inline_keyboard=admin_back_to_menu_kb)

conf_kb = [
    [InlineKeyboardButton(text="Реферальная система", callback_data="change_ref_percent")],
    [InlineKeyboardButton(text="Кошелек для вывода", callback_data="type_usdt_trc20")],
    [InlineKeyboardButton(text="‹ Назад", callback_data="back_to_admin_panel")]
]
conf_kb = InlineKeyboardMarkup(inline_keyboard=conf_kb)

