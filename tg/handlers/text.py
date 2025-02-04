menu_text = ("🛒 Магазин\n\n"
             "💰 Баланс: `{balance}` *₸*"
             "\n💲 Ваша скидка: *0%* и *0₸*")

magazine_text = ("🧾 *Формирование заказа*\n\n"
                 "Выберите, пожалуйста, город, в котором желаете приобрести товар:")

geo_text = ("🧾 *Формирование заказа*\n\n"
            "Выберите, пожалуйста, товар, который желаете приобрести:")

payment_text = ("🧾 *Формирование заказа*\n\n"
                "🏙 *Локация*: `{geo}`\n"
                "📦 *Товар*: `{product}`\n\n"
                "Выберите, пожалуйста, район:")

confirm_text = ("🧾 *Подтверждение заказа*\n\n"
                "🏙 *Локация*: `{geo}`\n"
                "📦 *Товар*: `{product}` {gram}\n\n"
                "💎 *Способ оплаты*: *₸*\n\n"
                "💲 *Стоимость*: {price}*₸*\n"
                "├ *Скидка на товар*: 0%\n"
                "├ *Ваши скидки*: 0% и 0*₸*\n"
                "├ *Кэшбэк за предыдущие покупки*: 0*₸*\n"
                "└ *Итого к оплате*: `{price}`*₸*\n\n\n"
                "_При выдаче реквизитов для оплаты сумма может повыситься, так как обменники берут дополнительную комиссию за обработку операций_.\n\n"
                "Если Вас все устраивает, подтвердите создание заказа:")

balance_confirm_text = ("🧾 *Подтверждение заказа*\n\n"
                "🏙 *Локация*: `{geo}`\n"
                "📦 *Товар*: `{product}` {gram}\n\n"
                "💎 *Способ оплаты*: *Баланс*\n\n"
                "💲 *Стоимость*: {price}*₸*\n"
                "├ *Скидка на товар*: 0%\n"
                "├ *Ваши скидки*: 0% и 0*₸*\n"
                "├ *Кэшбэк за предыдущие покупки*: 0*₸*\n"
                "└ *Итого к оплате*: `{price}`*₸*\n\n\n"
                "_При выдаче реквизитов для оплаты сумма может повыситься, так как обменники берут дополнительную комиссию за обработку операций_.\n\n"
                "Если Вас все устраивает, подтвердите создание заказа:")

order_text = ("🛒 *Заказ* #{order_id}\n\n"
              "Оплатите, пожалуйста, заказ по данным реквизитам:\n"
              "👛 *Кошелек*: `{req}`\n"
              "_Нажмите на кошелек, чтобы скопировать_\n"
              "💲 *Сумма для перевода*: `{kzt_sum}` *₸*\n"
              "_Нажмите на сумму, чтобы скопировать_\n\n\n"
              "*У вас есть 1juuuuuuuuujnmk`0 минут на оплату заявки, далее она отменится автоматически. "
              "Переводите точную сумму, в случае ошибки, заказ не будет выдан, а средства невозможно будет вернуть*.")

check_accepted = "♻️ *Ваш платёж принят в обработку, пожалуйста ожидайте*"

check_information = "*Если вы оплатили, отправьте чек для ускорения процесса*"

confirm_cancel = ("🔐 *Подтверждение отмены*\n\n"
                  "Вы уверены, что хотите отменить заявку?\n\n"
                  "‼️*Пожалуйста, убедитесь, что вы не оплачивали, в случае отмены, возврат средств и повторная проверка оплаты будет невозможна*.")


confirm_cancel_now = ("🔐 *Подтверждение отмены*\n\n"
                      "Вы уверены, что хотите отменить заявку?\n\n"
                      "‼️*Пожалуйста, убедитесь, что вы не оплачивали, в случае отмены, возврат средств и повторная проверка оплаты будет невозможна*.")


invoice_canceled = ("🔴 *Заявка отменена*\n\n"
                    "Ваша заявка был успешно отменена. В случае повторных множественных отмен, Ваш аккаунт будет заблокирован.")

add_balance_text = ("💰 *Пополнение баланса*\n\n"
                    "Введите, пожалуйста, сумму, на которую желаете пополнить баланс:")

choose_payment_balance = ("💰 *Пополнение баланса*\n\n"
                          "💲 *Сумма пополнения:* {amount}*₸*\n\n"
                          "Выберите, пожалуйста, наиболее удобный для Вас способ оплаты:")

confirm_balance_add = ("💰 *Пополнение баланса*\n\n"
                       "💲 *Сумма пополнения*: `{amount}`*₸*\n"
                       "💎 *Способ оплаты*: {method}\n\n"
                       "_При выдаче реквизитов для оплаты сумма может повыситься, так как обменники берут дополнительную комиссию за обработку операций_.\n\n"
                       "Если Вас все устраивает, подтвердите создание заказа:")

waiting_for_pay = ("💰 *Пополнение баланса*\n\n"
                   "💲 *Сумма пополнения*: `{amount}` *{symb}*\n"
                   "💎 *Способ оплаты*: {method}\n\n"
                   "Оплатите, пожалуйста, заказ по данным реквизитам:\n"
                   "👛 *Кошелек*: `{req}`\n"
                   "_Нажмите на кошелек, чтобы скопировать_\n"
                   "💲 *Сумма для перевода*: `{amount}` *{symb}*\n"
                   "_Нажмите на сумму, чтобы скопировать_\n\n"
                   "*У вас есть 10 минут на оплату заявки, далее она отменится автоматически.*\n"
                   "*Переводите точную сумму, в случае ошибки, баланс не будет пополнен, а средства невозможно будет вернуть.*\n\n")


add_balance_for_exchanger = ("Заявка #{inv_id}\n"
                             "💲 *Сумма пополнения*: `{amount}` *₸*\n"
                             "`{req_name}`\n"
                             "👛 *Кошелек*: `{req}`\n")


product_text = ("🧾 *Показ заказа*\n\n"
                "🏙 *Локация*: `{city}` `{rayon}`\n"
                "📦 *Товар*: `{product}` {gram}\n\n"
                "💎 *Способ оплаты*: *₸*\n\n"
                "💲 *Стоимость*: {price}*₸*\n"
                "├ *Скидка на товар*: 0%\n"
                "├ *Ваши скидки*: 0% и 0*₸*\n"
                "└  *Кэшбэк за предыдущие покупки*: 0*₸*\n\n"
                "`{address}`")

promo_text = ("🏷 *Промокод* \n\n"
                  "Здесь вы можете активировать промокод, который получили от администрации магазина, он может выдать Вам скидку в числовом или процентном эквиваленте.")
activating_promo = ("💊 *Активация промокода*\n\n"
                    "Введите, пожалуйста промокод:")
denied_promo = ("😢 *Промокод не найден или срок его действия истек*\n\n"
                "Нам очень жаль, но промокод недействителен.\n\n"
                "‼️ *Регистр важен при вводе промокода, соблюдайте порядок маленьких и больших букв.*")
ref_text = ("👥 *Реферальная программа* \n\n"
            "Ваша реферальная ссылка: {link}\n"
            "Привлечено пользователей: *{count}*\n\n"
            "Привлекайте пользователей в наш бот по вашей реферальной ссылке и зарабатывайте *{prc}%* от всех их покупок на "
            "свой внутренней баланс магазина, и получайте товар бесплатно!")

broadcast_text = ("✍️ *Рассылка*\n\n"
                  "Введите рассыламое сообщение:")

broadcasting_text = ("♻️ _Ведется рассылка_\n\n"
                     "✔️ *Отправлено*: {amount}\n"
                     "❌ *Заблокировано*: {b_amount}\n\n"
                     "🤖 _Отправка по персональным ботам_\n"
                     "✔️ *Отправлено*: {p_amount}\n"
                     "❌ *Заблокировано*: {p_b_amount}\n\n")


personal_bot_text = (
    '🤖 *Подключение собственного бота*\n\n'
    'Собственный бот позволит Вам всегда оставаться "в зоне покупок", '
    'при блокировке основного бота у Вас будет возможность приобрести товар в нем, таким образом - '
    'мы никогда не потеряем с Вами связь!\n\n'
    '*Инструкция по созданию и подключению бота:*\n\n'
    '*1.* Перейдите в бот - @botfather\n'
    '*2.* Нажмите кнопку "START"\n'
    '*3.* Введите команду `/newbot`\n'
    '*4.* Придумайте и введите название бота, название подойдет любое\n'
    '*5.* Придумайте и введите юзернейм (username) бота, '
    'подойдут любые латинские буквы, главное чтобы юзернейм оканчивался на "bot"\n'
    '*6.* Если Вы все сделали верно, Вам придет сообщение, которое начинается на:\n'
    '_Done! Congratulations on your new bot._\n\n'
    'В данном сообщении будет набор букв и цифр в формате:\n'
    '`1111111111:AAAAAAAAAAAAAA_GchLGbMkBdSBRIEspy11`\n\n'
    '*7.* Нажмите на данный текст, он скопирируется и пришлите его мне, после чего бот будет подключен.'
)

personal_bot_add_text = ("👌  *Бот успешно подключен*\n\n"
                         "Ваш бот: @{bot_user}\n\n"
                         "Теперь Вы можете совершать покупки и пользоваться нашим магазином в своем боте и не переживать, что потеряете с нами связь! Приятных покупок!")

find_user_text = ("🧐 *Поиск пользователя*\n\n"
                  "Отправьте @username или ID пользователя, или же перешлите его сообщение:")

profile_text = ("👤 *Пользователь:* `{user_id}`\n"
                "💰 *Баланс:* `{balance}` *₸*\n"
                "⚖️ *Покупок:* `{amount_pok}`\n"
                "💸 *Пополнений *: {amount_pop} *₸*\n\n"
                "📅 *Дата регистрации:* {date_reg}\n"
                "🎟 *Использованные промо:* `{amount_promo}`\n"
                "🎫 *Общая сумма промо*: `{sum_amount_promo}` *₸*\n\n"
                "🖇 *Реферальный код:* `{ref_code}`\n"
                "👥 *Пригласил:* {ref_user}")

add_remove_balance_text = ("➕➖ *Добавить/Убавить баланс*\n\n"
                           "*+ Добавление:* +2000\n"
                           "*- Убавление:* -2000\n"
                           "*= Указать:* 2000\n\n"
                           "Введите желаемое изменение баланса:")

stat_text = ("📊 *Статистика*\n\n"
             "👥 *Подключенные за 24ч:* `{con_24}`\n"
             "👥 *Подключенные за неделю:* `{con_ned}`\n"
             "👥 *Подключенные за месяц:* `{con_mes}`\n\n"
             "🛍 *Продажи за 24ч:* `{sell_24}`\n"
             "🛍 *Продажи за неделю:* `{sell_ned}`\n"
             "🛍 *Продажи за месяц:* `{sell_mes}`\n\n"
             "🤖 *Персональные боты:* `{pers_bots}`\n\n"
             "💰 *Поступило:* `{pos}`\n"
             "💸 *Выведено:* `{viv}`")

admin_panel_text = ("🔧 *Управление пользователями*\n"
                    "_Здесь можно искать пользователей, редактировать баланс, блокировать или разблокировать их, а также управлять промокодами и реферальной системой_.\n"
                    "📦 *Управление товарами*\n"
                    "_Добавляй, редактируй или удаляй товары, меняй цены и следи за наличием_!\n"
                    "💰 *Финансовые операции*\n"
                    "_Финансовый контроль в твоих руках_.\n"
                    "🤖 *Управление ботами*\n"
                    "_Подключай или отключай персональных ботов_.\n"
                    "📢 *Рассылки*\n"
                    "_Создавай массовые рассылки, чтобы всегда быть на связи с пользователями_.")

add_chapter_text = ("🗯 *Создание раздела продуктов*\n\n"
                    "Введите название раздела продуктов:")

added_title_chapter_text = "✔️ *Оформление раздела*"

add_city_text = ("🌇 *Добавление города*\n\n"
                 "Введите название города:")

shop_configuration_text = ("⚙️ *Настройки магазина*\n"
                           "_Управляй основными параметрами магазина, включая реферальную систему и интерфейс._\n"
                           "💸 *Реферальный процент*\n"
                           "_Настрой процент вознаграждения за реферальную систему._\n"
                           "🏪 *Название магазина*\n"
                           "_Измени отображаемое название магазина для пользователей._\n"
                           "🛠️ *Управление кнопками*\n"
                           "_В будущем здесь можно будет настраивать кнопки магазина._")

change_ref_text = ("🔢 *Изменение рефералки*\n\n"
                   "Укажите желаемый процент по рефералкам, например (`2.5`):")

transactions_text = ("⭐️ *Транзакция в сети* ⭐️\n\n"
                     "*Сумма USDT*: {usdt_sum}\n"
                     "*Курс USDT*: {course}\n"
                     "*Сумма KZT*: {kzt_sum}\n\n"
                     "`{txid}`")

usdt_trc20_text = ("💲 *Адрес крипто-кошелька*\n\n"
                   "Введите новый адрес для вывода USDT-TRC20:")

change_chapter_text = ("✍️ *Редактирование Раздела* \n\n"
                       "Выберите желаемый раздел:")

