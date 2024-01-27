from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from xjet import JetAPI


api = JetAPI(
    api_key="65aed6188f97a234d5f57bd9e0e4742ed12221838ef99c0362243a24371752f81e7f03ccc8556aca900013da",
    private_key="963da8c62a90d4ee44381547ca18a91b9845872776ef204b8a93ece5d684d192",
    network='mainnet'
)


API_ID = 27615235
API_HASH = '36274dce835701da2c8aec3d483048ed'
BOT_TOKEN = '6457192680:AAH-SuKcxXkdGe-tBWFYzO6Evt7-fqbWE8k'

app = Client("open_game_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Database setup and connection
import sqlite3

conn = sqlite3.connect('OpenDB.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance TEXT)')
conn.commit()


@app.on_message(filters.chat(-1001991663533) & filters.text)
async def handle_post(client, message):
    post_text = message.text
    if "⭐" in post_text:
        print(post_text)
        data = post_text.split(" ")
        user_id = data[2]
        balance_change = float(data[8])

        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        balance = float(cursor.fetchone()[0])

        balance_change += balance

        cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (balance_change, user_id))
        conn.commit()


@app.on_message(filters.command(['start']))
async def cmd_start(client, message):
    user_id = message.from_user.id
    cursor.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)', (user_id, 0.0))
    conn.commit()

    wallet_button = InlineKeyboardButton("👛 Кошелёк", callback_data='wallet')
    games_button = InlineKeyboardButton("🎮 Игры", callback_data='games')
    markup = InlineKeyboardMarkup([[wallet_button, games_button]])

    await message.reply("🚀 Играй, получая удовольствие и $OPEN!\n\n😉 Призы - не главное!", reply_markup=markup)


@app.on_callback_query()
async def callback_handler(client, callback_query):
    user_id = callback_query.from_user.id
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    balance = cursor.fetchone()[0]
    if callback_query.data == 'wallet':
        withdraw_button = InlineKeyboardButton("💸 Вывод", callback_data='withdraw')
        back_button = InlineKeyboardButton("♻️ Назад", callback_data='back')

        wallet_markup = InlineKeyboardMarkup([[withdraw_button, back_button]])

        await client.edit_message_text(text=f"⭐ Баланс: {round(balance, 3)} $OPEN", chat_id=callback_query.message.chat.id, message_id=callback_query.message.id, reply_markup=wallet_markup)

    elif callback_query.data == 'withdraw':
        back_button = InlineKeyboardButton("♻️ Назад", callback_data='back')

        markup = InlineKeyboardMarkup([[back_button]])
          
        if balance >= 10:
            cheque_url = await api.cheque_create(currency="open", amount=float(round(balance, 3)), description=f"⭐ Вывод из OpenGame!")
            balance_change = 0
            cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (balance_change, user_id))
            conn.commit()
            link_button = InlineKeyboardButton("👛 Активировать", url=cheque_url['external_link'])
            link_markup = InlineKeyboardMarkup([[link_button]])
            await client.edit_message_text(text=f"🚀 Чек на {round(balance, 3)} $OPEN\n\n✏️<b> жмите /start ПОСЛЕ того, как активировали чек!</b>", chat_id=callback_query.message.chat.id, message_id=callback_query.message.id, reply_markup=link_markup, parse_mode=enums.ParseMode.HTML)
        else:
            await client.edit_message_text(text=f"🤔 Минимальная сумма вывода: 10 $OPEN.", chat_id=callback_query.message.chat.id, message_id=callback_query.message.id, reply_markup=markup, parse_mode=enums.ParseMode.HTML)

    elif callback_query.data == 'games':
        game1 = InlineKeyboardButton("✏️ Виселица", callback_data='game1')
        back_button = InlineKeyboardButton("♻️ Назад", callback_data='back')

        markup = InlineKeyboardMarkup([[game1, back_button]])

        await client.edit_message_text(text=f"😉 Выберите игру из списка:", chat_id=callback_query.message.chat.id, message_id=callback_query.message.id, reply_markup=markup)

    elif callback_query.data == 'game1':
        play = InlineKeyboardButton("🚀 Играть", web_app=WebAppInfo(url="https://opencoingame.000webhostapp.com/"))
        back_button = InlineKeyboardButton("♻️ Назад", callback_data='back')

        markup = InlineKeyboardMarkup([[play, back_button]])

        await client.edit_message_text(text=f"✏️ Виселица\n\n🎮 Отгадайе слово с помощью подсказки и получите награду!\n\n💰Награда: 0.005 $OPEN за 1 букву!\n⚠️Штраф за ошибку: 5% от приза (макс. 25%)\n\n🚀 Приятной игры!", chat_id=callback_query.message.chat.id, message_id=callback_query.message.id, reply_markup=markup)

    elif callback_query.data == 'back':
        await client.delete_messages(callback_query.message.chat.id, callback_query.message.id)
        await cmd_start(client, callback_query.message)
        

if __name__ == '__main__':
    app.run()