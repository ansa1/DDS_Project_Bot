from peewee import *

db = SqliteDatabase('orders_and_couriers.db')


class Courier(Model):
    courier_id = IntegerField()

    class Meta:
        database = db


class Order(Model):
    client_id = IntegerField()
    priority = IntegerField()  # TODO add enum for priority
    status = IntegerField()  # TODO add enum for status
    text = CharField()
    courier = ForeignKeyField(Courier, related_name='orders', null=True)

    class Meta:
        database = db
