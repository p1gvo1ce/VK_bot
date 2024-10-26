import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import asyncio
import aiofiles
import json
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

async def get_text_from_file(filename):
    async with aiofiles.open(filename, mode='r') as f:
        token = await f.readline()
        return token.strip()

async def load_greeted_users(filename):
    try:
        async with aiofiles.open(filename, mode='r') as f:
            data = await f.read()
            return set(json.loads(data))
    except FileNotFoundError:
        return set()

async def save_greeted_users(filename, users):
    async with aiofiles.open(filename, mode='w') as f:
        await f.write(json.dumps(list(users)))

async def write_msg(vk, user_id, message, keyboard=None):
    loop = asyncio.get_event_loop()
    message_data = {'user_id': user_id, 'message': message, 'random_id': 0}
    if keyboard:
        message_data['keyboard'] = keyboard.get_keyboard()
    await loop.run_in_executor(None, vk.method, 'messages.send', message_data)

from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def get_start_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Новую", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("Перекрыть старую", color=VkKeyboardColor.PRIMARY)
    return keyboard

def get_new_tattoo_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Новую", color=VkKeyboardColor.PRIMARY)
    return keyboard

def get_old_tattoo_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Перекрыть старую", color=VkKeyboardColor.PRIMARY)
    return keyboard

async def main():
    token = await get_text_from_file("token.txt")
    vk = vk_api.VkApi(token=token)

    try:
        vk._auth_token()
        print("Подключение успешно!")
    except Exception as e:
        print(f"Ошибка при подключении: {e}")
        return

    group_id = await get_text_from_file('group_id.txt')
    print(f"Используется ID группы: {group_id}")

    try:
        longpoll = VkBotLongPoll(vk, group_id=group_id)
    except vk_api.exceptions.ApiError as e:
        print(f"Ошибка доступа: {e}. Проверь права доступа токена и убедитесь, что токен имеет права на работу с longpoll. Возможно, не хватает прав 'messages' или 'groups'.")
        print("Убедись, что функция LongPoll включена в настройках группы.")
        return

    users_greeted = await load_greeted_users("greeted_users.json")

    print("Бот запущен и готов к работе!")
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
            request = event.obj.message['text']
            user_id = event.obj.message['from_id']
            print(users_greeted)
            if user_id not in users_greeted:
                await write_msg(vk, user_id, "Здарова, быдло! Жмякай 'Начать', не тяни", get_start_keyboard())
                users_greeted.add(user_id)
                await save_greeted_users("greeted_users.json", users_greeted)
            else:
                # Обработка остальных сообщений
                if request.lower() == "начать":
                    await write_msg(vk, user_id, "Ты хочешь сделать новую татуировку или перекрыть старую? Че надо?", get_start_keyboard())
                elif request.lower() == "новую":
                    await write_msg(vk, user_id, "Ну и нахуй оно тебе надо? Акстись!", get_old_tattoo_keyboard())
                elif request.lower() == "перекрыть старую":
                    await write_msg(vk, user_id, "Заебал, и так норм. А если деньги лишние, то скинь их просто так или слей в казино, заебал.", get_new_tattoo_keyboard())
                else:
                    await write_msg(vk, user_id, "Не понял вашего ответа...")

if __name__ == "__main__":
    asyncio.run(main())
