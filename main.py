from dialog_bot_sdk.bot import DialogBot
from models import User
from handlers import utils
from handlers.regular import *
import grpc
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN") or ""
ENDPOINT = os.environ.get("ENDPOINT") or "hackathon-mob.transmit.im"


def on_click(*params):
    if params[0].id == "main_menu":
        menu_handler(bot, params)

    elif params[0].id == "cancel":
        utils.cancel_handler(bot, params)

    elif params[0].id == "cost_list":
        spend_list_handler(bot, params)

    elif params[0].id == "cost_manager":
        cost_manager_handler(bot, params)

    elif params[0].id == "delete_all":
        delete_all_handler(bot, params)


def on_msg(*params):
    if not User.select().where(User.uid == params[0].sender_uid).exists():
        new_user_handler(bot, params)
        return

    state = User.select().where(User.uid == params[0].sender_uid).get().state

    if params[0].message.textMessage.text == "/cancel" or params[0].message.textMessage.text == "/menu":
        utils.cancel_handler(bot, params)

    elif state == "MONTHLY_BALANCE_SET":
        balance_set_handler(bot, params)

    elif state == "NEW_SPEND_COST" or state == "NEW_SPEND_NAME":
        new_spend_handler(bot, params)

    elif state == "EDIT_SPEND_COST":
        edit_spend_cost_handler(bot, params)

    elif state == "EDIT_SPEND_NAME":
        edit_spend_name_handler(bot, params)

    else:
        unknown_message_handler(bot, params)


if __name__ == '__main__':
    bot = DialogBot.get_secure_bot(
        ENDPOINT,  # bot endpoint from environment
        grpc.ssl_channel_credentials(),  # SSL credentials (empty by default!)
        BOT_TOKEN  # bot token from environment
    )

    bot.messaging.on_message(on_msg, on_click)
