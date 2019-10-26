from dialog_bot_sdk import interactive_media
from dialog_bot_sdk.bot import DialogBot
from models import User, BalanceChange


def set_state_by_uid(uid: int, state: str):
    user = User.select().where(User.uid == uid).get()
    user.state = state
    user.save()


def cancel_handler(bot: DialogBot, params):
    try:
        bot.messaging.send_message(
            params[0].peer,
            "Отправляю вас в главное меню",
            get_default_layout()
        )

        set_state_by_uid(params[0].sender_uid, "START")
    except (AttributeError, KeyError):
        bot.messaging.send_message(
            bot.users.get_user_peer_by_id(params[0].uid),
            "Отправляю вас в главное меню",
            get_default_layout()
        )

        set_state_by_uid(params[0].uid, "START")


def get_default_layout():
    return [interactive_media.InteractiveMediaGroup(
        [
            interactive_media.InteractiveMedia(
                "main_menu",
                interactive_media.InteractiveMediaButton("update_budget", "Изменить бюджет офиса")
            ),
            interactive_media.InteractiveMedia(
                "main_menu",
                interactive_media.InteractiveMediaButton("create_spend", "Добавить трату")
            ),
            interactive_media.InteractiveMedia(
                "main_menu",
                interactive_media.InteractiveMediaButton("list_spends", "Удалить или изменить траты")
            ),
            interactive_media.InteractiveMedia(
                "main_menu",
                interactive_media.InteractiveMediaButton("export_xlsx", "Экспортировать данные в табличный вид")
            )
        ]
    )]


def get_spend_sum(uid: int):
    sum = 0
    for spend in BalanceChange.select().where(BalanceChange.owner == uid):
        sum += spend.cost
    return sum


def get_spends_list(uid: int):
    costs = {}

    for cost in BalanceChange.select().where(BalanceChange.owner == uid).order_by(BalanceChange.name):
        costs[str(cost.get_id())] = f"{cost.name}"

    return [interactive_media.InteractiveMediaGroup(
        [interactive_media.InteractiveMedia(
            "cost_list",
            interactive_media.InteractiveMediaSelect(
                costs,
                label="Список трат"
            )
        ),
            interactive_media.InteractiveMedia(
                "cancel",
                interactive_media.InteractiveMediaButton("cancel", "В главное меню")
            ),
            interactive_media.InteractiveMedia(
                "delete_all",
                interactive_media.InteractiveMediaButton("delete_all", "Удалить ВСЕ траты")
            )

        ]
    )]

def get_list_management_menu(id: int):
    return [interactive_media.InteractiveMediaGroup(
        [
            interactive_media.InteractiveMedia(
                "cost_manager",
                interactive_media.InteractiveMediaButton(f"delete_{id}", "Удалить трату")
            ),
            interactive_media.InteractiveMedia(
                "cost_manager",
                interactive_media.InteractiveMediaButton(f"name_{id}", "Изменить название траты")
            ),
            interactive_media.InteractiveMedia(
                "cost_manager",
                interactive_media.InteractiveMediaButton(f"cost_{id}", "Изменить сумму траты")
            ),
            interactive_media.InteractiveMedia(
                "main_menu",
                interactive_media.InteractiveMediaButton("list_spends", "Назад к списку трат")
            )
        ]
    )

    ]