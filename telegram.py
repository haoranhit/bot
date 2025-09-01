import requests

# ==== 配置你的 Bot Token 和 Chat ID ====
BOT_TOKEN = "8024666853:AAG6QwcWOD0IIt6LZ9qoRVzT0Hj58lZaPkY"
CHAT_ID = 8335011829  # 你从 @userinfobot 得到的 ID

# ==== 要发送的消息 ====
message = "Hello from Visa bot!"

# ==== 发送消息 ====
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": message
}

response = requests.post(url, data=payload)
print(response.text)