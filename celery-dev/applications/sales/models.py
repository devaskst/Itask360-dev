from peewee import *
import datetime
from os import getenv
import sys
import inspect
# USER = getenv("POSTGRES_USER", "itask")
# PASSWORD = getenv("POSTGRES_PASSWORD", "12345678910")
# PORT = getenv("POSTGRES_PORT", 5430)
# HOST = "localhost"
# DB_NAME = getenv("POSTGRES_DB", "wow")

# db = PostgresqlDatabase(DB_NAME, user=USER, password=PASSWORD, port=PORT, host=HOST)

from database import db, db_user

def create_views():
    db.execute_sql('''
    CREATE OR REPLACE VIEW sales.active_sales 
        AS SELECT retaildemand.id,
            'Заказ '::text || retaildemand.code::text AS value,
             status.name AS description
        FROM sales.retaildemand
        INNER JOIN sales.status ON sales.status.id = sales.retaildemand.status_id
        WHERE status.name::text = ANY (ARRAY['Новый'::character varying::text, 
            'Подтверждён'::character varying::text, 'В сборке'::character varying::text])
        ORDER BY status.name''')

def create_all_tables():
    db.connect(reuse_if_open=True)
    db.execute_sql(f'CREATE SCHEMA IF NOT EXISTS sales AUTHORIZATION {db_user}')
    for cls in sys.modules[__name__].__dict__.values():
        if hasattr(cls, '__bases__') and inspect.isclass(cls) and issubclass(cls, Model):
            if cls is not Base and cls is not Model:
                cls.create_table()
    create_views()
    db.close()

class Base(Model):
    class Meta:
        database = db
        schema = 'sales'


class Status(Base):
    id = UUIDField(primary_key=True, null=False)
    name = CharField(max_length=255, null=False)


class Retaildemand(Base):
    id = UUIDField(primary_key=True, null=False)
    status = ForeignKeyField(Status, on_delete="RESTRICT")
    code = IntegerField(null=False)
    created = DateTimeField(default=datetime.datetime.utcnow, null=False)
    collected = DateTimeField(null=True)
    comment = TextField(null=True)
    account_id = UUIDField(null=False)
    retail_store = CharField(max_length=255, null=False)


class Product(Base):
    id = UUIDField(primary_key=True, null=False)
    name = CharField(max_length=255, null=False)


class RetaildemandProduct(Model):
    product = ForeignKeyField(Product, on_delete="RESTRICT")
    retaildemand = ForeignKeyField(Retaildemand, on_delete="CASCADE")
    quantity = IntegerField(null=False, default=1)

    class Meta:
        database = db
        db_table = "retaildemand_product"
        primary_key = CompositeKey("product", "retaildemand")


def create_statuses():
    from uuid import uuid4

    statuses = ("Новый", "Подтверждён", "В сборке", "Готов к выдаче", "Выдан")
    uuids = [uuid4() for _ in range(len(statuses))]
    return Status.insert_many(zip(uuids, statuses), [Status.id, Status.name]).execute()


def create_retaildemand():
    from uuid import uuid4
    from random import choice, randint, random
    from datetime import datetime, timedelta

    st_ids = create_statuses()
    acc_ids = [uuid4() for _ in range(10)]
    rows = []
    for _ in range(100):
        id = uuid4()
        status_id = choice(st_ids)
        code = randint(1, 1000)
        created = datetime.utcnow() - timedelta(
            hours=randint(0, 5), minutes=randint(10, 59)
        )
        collected = None
        if random() < 0.3:
            collected = created + timedelta(
                hours=randint(0, 5), minutes=randint(10, 59)
            )
        comment = ""
        if random() < 0.1:
            comment = "Сборщики! Будьте аккуратны, товар хрупкий!"
        account_id = choice(acc_ids)
        retail_store = choice(["Онлайн", "Точка 1", "Точка 2", "Точка 3"])
        rows.append(
            (id, status_id, code, created, collected, comment, account_id, retail_store)
        )

    return Retaildemand.insert_many(
        rows,
        [
            Retaildemand.id,
            Retaildemand.status,
            Retaildemand.code,
            Retaildemand.created,
            Retaildemand.collected,
            Retaildemand.comment,
            Retaildemand.account_id,
            Retaildemand.retail_store,
        ],
    ).execute()


def create_products():
    import requests
    from uuid import uuid4

    names = [
        d["title"]
        for d in requests.get("https://api.escuelajs.co/api/v1/products").json()
    ]
    uuids = [uuid4() for _ in range(len(names))]
    return Product.insert_many(zip(names, uuids), [Product.name, Product.id]).execute()


def create_retaildemand_product():
    from random import choices, randint

    product_ids = create_products()
    retaildemand_ids = create_retaildemand()

    rows = []

    for ret_id in retaildemand_ids:
        prod_id = set(choices(product_ids, k=randint(1, 10)))
        quantity = randint(1, 10)
        for p_id in prod_id:
            rows.append((ret_id, p_id, quantity))

    RetaildemandProduct.insert_many(
        rows,
        [
            RetaildemandProduct.retaildemand,
            RetaildemandProduct.product,
            RetaildemandProduct.quantity,
        ],
    ).execute()


def create_db_and_data():
    with db.atomic():
        create_retaildemand_product()


# create_db_and_data()