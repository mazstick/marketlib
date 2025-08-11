from pyrogram import Client

API_ID = 23093322 # Replace with your API ID
API_HASH = "bad200d6e9b33ae67d9460f1ba8d63b3"          # Replace with your API Hash
BOT_TOKEN = "7886830075:AAFccEFAqZ0JnZEo442TekxVcZ7CSZE-_t8"        # Replace with your Bot Token

# UPLOAD_FILE = "test.csv"         # File in current directory

# === INIT ===
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

with app:
    channel_chat_id = -1002893725768
    disc_chat_id = -1002710617476
    app.send_message(channel_chat_id, "Hello from my bot!")