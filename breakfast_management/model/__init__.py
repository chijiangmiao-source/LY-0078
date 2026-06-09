# -*- coding: utf-8 -*-
from sqlobject import SQLObject, StringCol, IntCol, DateTimeCol, DateCol, ForeignKey, BoolCol, MultipleJoin
from sqlobject.col import EnumCol
from datetime import datetime, date


class User(SQLObject):
    class sqlmeta:
        table = 'users'

    username = StringCol(length=50, unique=True, notNone=True)
    password = StringCol(length=255, notNone=True)
    real_name = StringCol(length=50)
    role = EnumCol(enumValues=['admin', 'kitchen', 'delivery'], default='delivery')
    is_active = BoolCol(default=True)
    created_at = DateTimeCol(default=datetime.now)


class Room(SQLObject):
    class sqlmeta:
        table = 'rooms'

    room_number = StringCol(length=20, unique=True, notNone=True)
    room_type = EnumCol(enumValues=['single', 'double', 'suite', 'family'], default='double')
    floor = IntCol(default=1)
    status = EnumCol(enumValues=['vacant', 'occupied', 'maintenance'], default='vacant')
    notes = StringCol(length=500, default='')
    created_at = DateTimeCol(default=datetime.now)

    guests = MultipleJoin('Guest')


class Guest(SQLObject):
    class sqlmeta:
        table = 'guests'

    name = StringCol(length=50, notNone=True)
    id_card = StringCol(length=20)
    phone = StringCol(length=20)
    room = ForeignKey('Room', notNone=True)
    check_in_date = DateCol(notNone=True, default=date.today)
    check_out_date = DateCol(default=None)
    breakfast_included = BoolCol(default=True)
    package_type = ForeignKey('BreakfastPackage', default=None)
    status = EnumCol(enumValues=['checked_in', 'checked_out'], default='checked_in')
    notes = StringCol(length=500, default='')
    created_at = DateTimeCol(default=datetime.now)


class BreakfastPackage(SQLObject):
    class sqlmeta:
        table = 'breakfast_packages'

    name = StringCol(length=100, unique=True, notNone=True)
    code = StringCol(length=20, unique=True, notNone=True)
    description = StringCol(length=500, default='')
    price = IntCol(default=0)
    items = StringCol(length=1000, default='')
    is_active = BoolCol(default=True)
    created_at = DateTimeCol(default=datetime.now)


class Basket(SQLObject):
    class sqlmeta:
        table = 'baskets'

    basket_code = StringCol(length=50, unique=True, notNone=True)
    package_type = ForeignKey('BreakfastPackage', default=None)
    kitchen = EnumCol(enumValues=['kitchen_a', 'kitchen_b'], default='kitchen_a')
    status = EnumCol(enumValues=['available', 'in_use', 'cleaning', 'disabled'], default='available')
    last_clean_date = DateCol(default=date.today)
    notes = StringCol(length=500, default='')
    created_at = DateTimeCol(default=datetime.now)


class PreparationSchedule(SQLObject):
    class sqlmeta:
        table = 'preparation_schedules'

    schedule_date = DateCol(notNone=True, default=date.today)
    time_slot = EnumCol(enumValues=['early', 'morning', 'late'], notNone=True)
    package_type = ForeignKey('BreakfastPackage', notNone=True)
    quantity = IntCol(notNone=True, default=0)
    prepared_by = ForeignKey('User', default=None)
    status = EnumCol(enumValues=['pending', 'preparing', 'completed'], default='pending')
    completed_at = DateTimeCol(default=None)
    notes = StringCol(length=500, default='')
    created_at = DateTimeCol(default=datetime.now)


class BasketAssembly(SQLObject):
    class sqlmeta:
        table = 'basket_assemblies'

    basket = ForeignKey('Basket', notNone=True)
    schedule = ForeignKey('PreparationSchedule', notNone=True)
    assembled_by = ForeignKey('User', notNone=True)
    assembled_at = DateTimeCol(default=datetime.now)
    status = EnumCol(enumValues=['assembled', 'delivered', 'returned'], default='assembled')
    notes = StringCol(length=500, default='')


class DeliveryRecord(SQLObject):
    class sqlmeta:
        table = 'delivery_records'

    delivery_no = StringCol(length=50, unique=True, notNone=True)
    room = ForeignKey('Room', notNone=True)
    guest = ForeignKey('Guest', default=None)
    basket = ForeignKey('Basket', notNone=True)
    time_slot = EnumCol(enumValues=['early', 'morning', 'late'], notNone=True)
    delivery_date = DateCol(notNone=True, default=date.today)
    delivery_person = ForeignKey('User', default=None)
    dispatched_at = DateTimeCol(default=None)
    delivered_at = DateTimeCol(default=None)
    returned_at = DateTimeCol(default=None)
    status = EnumCol(
        enumValues=['pending', 'delivering', 'delivered', 'returned', 'cancelled'],
        default='pending'
    )
    notes = StringCol(length=500, default='')
    created_at = DateTimeCol(default=datetime.now)
    signatory = StringCol(length=50, default='')
    signed_at = DateTimeCol(default=None)
    sign_status = EnumCol(enumValues=['unsigned', 'signed', 'rejected'], default='unsigned')
    sign_notes = StringCol(length=500, default='')
    sign_modified_by = StringCol(length=100, default='')
    sign_modified_at = DateTimeCol(default=None)
    sign_modify_history = StringCol(length=2000, default='')


class Ingredient(SQLObject):
    class sqlmeta:
        table = 'ingredients'

    name = StringCol(length=100, unique=True, notNone=True)
    unit = StringCol(length=20, default='')
    category = StringCol(length=50, default='')
    is_active = BoolCol(default=True)
    notes = StringCol(length=500, default='')
    created_at = DateTimeCol(default=datetime.now)


class PreparationMaterial(SQLObject):
    class sqlmeta:
        table = 'preparation_materials'

    prep_date = DateCol(notNone=True, default=date.today)
    time_slot = EnumCol(enumValues=['early', 'morning', 'late'], notNone=True)
    package_type = ForeignKey('BreakfastPackage', notNone=True)
    ingredient = ForeignKey('Ingredient', notNone=True)
    schedule = ForeignKey('PreparationSchedule', default=None)
    planned_qty = IntCol(notNone=True, default=0)
    actual_qty = IntCol(default=0)
    status = EnumCol(
        enumValues=['pending', 'preparing', 'completed', 'cancelled'],
        default='pending'
    )
    prepared_by = ForeignKey('User', default=None)
    completed_at = DateTimeCol(default=None)
    notes = StringCol(length=500, default='')
    created_at = DateTimeCol(default=datetime.now)


class WasteRecord(SQLObject):
    class sqlmeta:
        table = 'waste_records'

    waste_date = DateCol(notNone=True, default=date.today)
    time_slot = EnumCol(enumValues=['early', 'morning', 'late'], notNone=True)
    package_type = ForeignKey('BreakfastPackage', notNone=True)
    stage = EnumCol(
        enumValues=['preparation', 'assembly', 'delivery', 'return'],
        notNone=True,
        default='preparation'
    )
    quantity = IntCol(notNone=True, default=0)
    reason = StringCol(length=200, default='')
    registered_by = ForeignKey('User', default=None)
    schedule = ForeignKey('PreparationSchedule', default=None)
    material = ForeignKey('PreparationMaterial', default=None)
    delivery = ForeignKey('DeliveryRecord', default=None)
    notes = StringCol(length=500, default='')
    created_at = DateTimeCol(default=datetime.now)


def _ensure_column(conn, table_name, col_def):
    try:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_def}")
    except Exception:
        pass


def init_model(sqlhub_ref):
    try:
        User.createTable(ifNotExists=True)
        Room.createTable(ifNotExists=True)
        BreakfastPackage.createTable(ifNotExists=True)
        Basket.createTable(ifNotExists=True)
        Guest.createTable(ifNotExists=True)
        PreparationSchedule.createTable(ifNotExists=True)
        BasketAssembly.createTable(ifNotExists=True)
        DeliveryRecord.createTable(ifNotExists=True)
        Ingredient.createTable(ifNotExists=True)
        PreparationMaterial.createTable(ifNotExists=True)
        WasteRecord.createTable(ifNotExists=True)

        conn = sqlhub_ref.getConnection()
        _ensure_column(conn, 'delivery_records', "signatory VARCHAR(50) DEFAULT ''")
        _ensure_column(conn, 'delivery_records', "signed_at TIMESTAMP")
        _ensure_column(conn, 'delivery_records', "sign_status VARCHAR(20) DEFAULT 'unsigned'")
        _ensure_column(conn, 'delivery_records', "sign_notes VARCHAR(500) DEFAULT ''")
        _ensure_column(conn, 'delivery_records', "sign_modified_by VARCHAR(100) DEFAULT ''")
        _ensure_column(conn, 'delivery_records', "sign_modified_at TIMESTAMP")
        _ensure_column(conn, 'delivery_records', "sign_modify_history VARCHAR(2000) DEFAULT ''")

        if not User.selectBy(username='admin').count():
            from breakfast_management.lib.security import hash_password
            pwd = hash_password('admin123')
            User(
                username='admin',
                password=pwd,
                real_name='系统管理员',
                role='admin',
                is_active=True
            )
    except Exception as e:
        print(f"Init model warning: {e}")
