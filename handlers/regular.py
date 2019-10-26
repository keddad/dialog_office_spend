from dialog_bot_sdk.bot import DialogBot
from models import User, BalanceChange
from handlers import utils
from openpyxl import Workbook
from pathlib import Path

SPEND_CACHE = {}
EVENT_LIST_MESSAGE_CACHE = {}
COST_EDIT_CACHE = {}


def unknown_message_handler(bot: DialogBot, params):
    try:
        peer = bot.users.get_user_peer_by_id(params[0].uid)
    except AttributeError:
        peer = params[0].peer

    bot.messaging.send_message(
        peer,
        "Я не понимаю, что ты хочешь сделать. Можешь написать /menu для возврата в главное меню"
    )


def error_handler(bot: DialogBot, params):
    try:
        peer = bot.users.get_user_peer_by_id(params[0].uid)
    except AttributeError:
        peer = params[0].peer

    bot.messaging.send_message(
        peer,
        "Кажется, что то сломалось. Возвращаемся в главное меню"
    )

    utils.cancel_handler(bot, params)


def new_user_handler(bot: DialogBot, params):
    """
    Обработчик для новых пользователей, возвращающий приветственное сообщение
    """

    bot.messaging.send_message(
        params[0].peer,
        "Привет. Кажется, ты еще не зарегестрирован. Укажи месячный бюджет офиса"
    )

    user = User.create(
        uid=params[0].sender_uid
    )
    user.save()

    utils.set_state_by_uid(params[0].sender_uid, "MONTHLY_BALANCE_SET")


def balance_set_handler(bot: DialogBot, params):
    try:
        peer = params[0].peer
    except (AttributeError, KeyError):
        peer = bot.users.get_user_peer_by_id(params[0].uid)

    try:
        new_balance = int(params[0].message.textMessage.text)
    except ValueError:
        bot.messaging.send_message(
            peer,
            "Не могу тебя понять. Пожалуйста, отправь положительное число без дополнительных символов, только цифры"
        )
        return

    if new_balance < 0:
        bot.messaging.send_message(
            peer,
            "Не могу тебя понять. Пожалуйста, отправь положительное число без дополнительных символов, только цифры"
        )
        return

    user = User.select().where(User.uid == params[0].sender_uid).get()
    user.monthly_balance = new_balance
    user.save()

    bot.messaging.send_message(
        peer,
        "Баланс обновлен"
    )

    utils.cancel_handler(bot, params)


def new_spend_handler(bot: DialogBot, params):
    peer = params[0].peer
    state = User.select().where(User.uid == params[0].sender_uid).get().state

    if state == "NEW_SPEND_NAME":
        name = params[0].message.textMessage.text

        SPEND_CACHE[params[0].sender_uid] = {
            "owner": params[0].sender_uid,
            "name": name,
        }

        bot.messaging.send_message(
            peer,
            "Укажите стоймость траты"
        )

        utils.set_state_by_uid(params[0].sender_uid, "NEW_SPEND_COST")

    elif state == "NEW_SPEND_COST":
        try:
            cost = int(params[0].message.textMessage.text)
        except ValueError:
            bot.messaging.send_message(
                peer,
                "Не могу тебя понять. Пожалуйста, отправь положительное число без дополнительных символов, только цифры"
            )
            return

        if cost < 0:
            bot.messaging.send_message(
                peer,
                "Не могу тебя понять. Пожалуйста, отправь положительное число без дополнительных символов, только цифры"
            )
            return

        SPEND_CACHE[params[0].sender_uid]["cost"] = cost

        new_spend = BalanceChange.create(
            **SPEND_CACHE[params[0].sender_uid]
        )
        new_spend.save()

        del SPEND_CACHE[params[0].sender_uid]

        bot.messaging.send_message(
            peer,
            "Трата успешно добавлена"
        )

        spending = utils.get_spend_sum(params[0].sender_uid)
        user_budget = User.select().where(User.uid == params[0].sender_uid).get().monthly_balance

        if spending > user_budget:
            bot.messaging.send_message(
                peer,
                f"Предупреждение: вы превысили лимит трат на {spending - user_budget}"
            )

        else:
            bot.messaging.send_message(
                peer,
                f"Остаток бюджета - {user_budget - spending}"
            )

        utils.cancel_handler(bot, params)


def menu_handler(bot: DialogBot, params):
    peer = bot.users.get_user_peer_by_id(params[0].uid)

    if params[0].value == "update_budget":
        bot.messaging.send_message(
            peer,
            "Укажите новый бюджет"
        )

        utils.set_state_by_uid(params[0].uid, "MONTHLY_BALANCE_SET")

    elif params[0].value == "create_spend":
        bot.messaging.send_message(
            peer,
            "Как назвать трату?"
        )

        utils.set_state_by_uid(params[0].uid, "NEW_SPEND_NAME")

    elif params[0].value == "list_spends":
        bot.messaging.send_message(
            peer,
            "Список трат",
            utils.get_spends_list(params[0].uid)
        )


    elif params[0].value == "export_xlsx":
        bot.messaging.send_message(
            peer,
            "Ваша таблица:"
        )

        wb = Workbook()
        ws = wb.active

        ws.append(["Название", "Цена", "Дата добавления"])

        for spend in BalanceChange.select().where(BalanceChange.owner == params[0].uid):
            ws.append([spend.name, spend.cost, spend.added])

        wb.save(f"sheets/{params[0].uid}.xlsx")

        bot.messaging.send_file(
            peer,
            f"sheets/{params[0].uid}.xlsx"
        )

        object = Path(f"sheets/{params[0].uid}.xlsx")
        object.unlink()

        utils.cancel_handler(bot, params)


def spend_list_handler(bot: DialogBot, params):
    spend_id = int(params[0].value)
    peer = bot.users.get_user_peer_by_id(params[0].uid)
    EVENT_LIST_MESSAGE_CACHE[params[0].uid] = params[0]

    bot.messaging.send_message(
        peer,
        "Выберите действие",
        utils.get_list_management_menu(spend_id)
    )


def cost_manager_handler(bot: DialogBot, params):
    task, cost_id = params[0].value.split("_")
    cost_id = int(cost_id)
    peer = bot.users.get_user_peer_by_id(params[0].uid)

    if task == "delete":
        bot.messaging.delete(
            params[0]
        )

        cost = BalanceChange.select().where(BalanceChange.id == cost_id).get()
        cost.delete_instance()

        if params[0].uid in EVENT_LIST_MESSAGE_CACHE:
            bot.messaging.update_message(
                EVENT_LIST_MESSAGE_CACHE[params[0].uid],
                "Список трат",
                utils.get_spends_list(params[0].uid)
            )

        bot.messaging.send_message(
            peer,
            "Событие удалено"
        )

        utils.cancel_handler(bot, params)

    elif task == "name":
        bot.messaging.send_message(
            peer,
            "Укажите новое имя траты"
        )

        COST_EDIT_CACHE[params[0].uid] = cost_id

        utils.set_state_by_uid(params[0].uid, "EDIT_SPEND_NAME")

    elif task == "cost":
        bot.messaging.send_message(
            peer,
            "Укажите новую цену траты"
        )

        COST_EDIT_CACHE[params[0].uid] = cost_id

        utils.set_state_by_uid(params[0].uid, "EDIT_SPEND_COST")


def edit_spend_cost_handler(bot: DialogBot, params):
    peer = params[0].peer

    try:
        cost = int(params[0].message.textMessage.text)
    except ValueError:
        bot.messaging.send_message(
            peer,
            "Не могу тебя понять. Пожалуйста, отправь положительное число без дополнительных символов, только цифры"
        )
        return

    if cost < 0:
        bot.messaging.send_message(
            peer,
            "Не могу тебя понять. Пожалуйста, отправь положительное число без дополнительных символов, только цифры"
        )
        return

    balance_change = BalanceChange.select().where(BalanceChange.id == COST_EDIT_CACHE[params[0].sender_uid]).get()
    balance_change.cost = cost
    balance_change.save()

    bot.messaging.send_message(
        peer,
        "Данные обновлены"
    )

    utils.cancel_handler(bot, params)


def edit_spend_name_handler(bot: DialogBot, params):
    peer = params[0].peer
    new_name = params[0].message.textMessage.text

    balance_change = BalanceChange.select().where(BalanceChange.id == COST_EDIT_CACHE[params[0].sender_uid]).get()
    balance_change.name = new_name
    balance_change.save()

    bot.messaging.send_message(
        peer,
        "Данные обновлены"
    )

    if params[0].sender_uid in EVENT_LIST_MESSAGE_CACHE:
        bot.messaging.update_message(
            EVENT_LIST_MESSAGE_CACHE[params[0].sender_uid],
            "Список трат",
            utils.get_spends_list(params[0].sender_uid)
        )

    utils.cancel_handler(bot, params)


def delete_all_handler(bot: DialogBot, params):
    peer = bot.users.get_user_peer_by_id(params[0].uid)

    for cost in BalanceChange.select().where(BalanceChange.owner == params[0].uid):
        cost.delete_instance()

    bot.messaging.send_message(
        peer,
        "Все траты были успешно удалены"
    )

    bot.messaging.delete(
        params[0]
    )

    utils.cancel_handler(bot, params)
