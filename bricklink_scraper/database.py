import datetime as dt
from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    FloatField,
    IntegerField,
    ForeignKeyField,
    DateTimeField,
)
from config import SQLITE_DATABASE

db = SqliteDatabase(SQLITE_DATABASE)


class BaseModel(Model):
    class Meta:
        database = db


class Category(BaseModel):
    name = CharField(null=False)
    category_id = CharField(null=False, unique=True)
    # Support of other item types can be implemented by adding item_type
    # column; in this case the combination of item_type and category_id needs
    # to be unique. Item types: S - Sets, P - Parts, M - Minifigures,
    # B - Books, G - Gear, C - Catalogs, I - Instructions, O - Original Boxes
    # item_type = CharField(null=False, choices=["S", "P", "M", "B", "G", "C", "I", "O"])


class Part(BaseModel):
    item_id = CharField(null=False, unique=True)
    item_name = CharField(1000, null=False)
    category = ForeignKeyField(Category, backref="parts", null=False)
    weight = FloatField(null=True)
    scrape_timestamp = DateTimeField(null=False, default=dt.datetime.now)


class ColoredPart(BaseModel):
    part = ForeignKeyField(Part, backref="colored_parts", null=False)
    color_id = CharField(null=False)
    color_name = CharField(null=False)
    color_rgb = CharField(null=False)
    # All prices in EURO in hundredths of cents e.g. 1.45 -> 14500
    six_month_new_times_sold = IntegerField(null=True)
    six_month_new_total_qty = IntegerField(null=True)
    six_month_new_min_price = IntegerField(null=True)
    six_month_new_avg_price = IntegerField(null=True)
    six_month_new_qty_avg_price = IntegerField(null=True)
    six_month_new_max_price = IntegerField(null=True)
    six_month_used_times_sold = IntegerField(null=True)
    six_month_used_total_qty = IntegerField(null=True)
    six_month_used_min_price = IntegerField(null=True)
    six_month_used_avg_price = IntegerField(null=True)
    six_month_used_qty_avg_price = IntegerField(null=True)
    six_month_used_max_price = IntegerField(null=True)
    current_new_total_lots = IntegerField(null=True)
    current_new_total_qty = IntegerField(null=True)
    current_new_min_price = IntegerField(null=True)
    current_new_avg_price = IntegerField(null=True)
    current_new_qty_avg_price = IntegerField(null=True)
    current_new_max_price = IntegerField(null=True)
    current_used_total_lots = IntegerField(null=True)
    current_used_total_qty = IntegerField(null=True)
    current_used_min_price = IntegerField(null=True)
    current_used_avg_price = IntegerField(null=True)
    current_used_qty_avg_price = IntegerField(null=True)
    current_used_max_price = IntegerField(null=True)
    scrape_timestamp = DateTimeField(default=dt.datetime.now)


db.create_tables([Category, Part, ColoredPart])
