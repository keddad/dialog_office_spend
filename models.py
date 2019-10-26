import peewee
import datetime

database = peewee.SqliteDatabase("db.db")


class User(peewee.Model):
    uid = peewee.IntegerField()
    state = peewee.CharField(default="START")
    monthly_balance = peewee.IntegerField(default=0)

    class Meta:
        database = database


class BalanceChange(peewee.Model):
    owner = peewee.IntegerField()
    cost = peewee.IntegerField()
    name = peewee.CharField()
    added = peewee.DateField(default=datetime.date.today())

    class Meta:
        database = database


database.create_tables([User, BalanceChange])
