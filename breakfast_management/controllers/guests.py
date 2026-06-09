# -*- coding: utf-8 -*-
from tg import expose, request, redirect, url
from breakfast_management.controllers.base import BaseController, require_login, _flash
from breakfast_management.model import Guest, Room, BreakfastPackage
from sqlobject import AND, OR
from datetime import date, datetime


class GuestsController(BaseController):

    @expose('breakfast_management.templates.guests.index')
    @require_login
    def index(self, **kw):
        query = Guest.select()
        if kw.get('keyword'):
            keyword = kw['keyword'].strip()
            query = Guest.select(OR(
                Guest.q.name.contains(keyword),
                Guest.q.phone.contains(keyword),
                Guest.q.id_card.contains(keyword)
            ))
        if kw.get('status'):
            query = Guest.select(AND(query.expression, Guest.q.status == kw['status']))
        if kw.get('room_id'):
            query = Guest.select(AND(query.expression, Guest.q.roomID == int(kw['room_id'])))

        guests = list(query.orderBy(Guest.q.check_in_date))
        rooms = list(Room.select().orderBy(Room.q.room_number))
        return self._get_context(
            page='guests',
            guests=guests,
            rooms=rooms,
            filters=kw
        )

    @expose('breakfast_management.templates.guests.form')
    @require_login
    def new(self, **kw):
        rooms = list(Room.select().orderBy(Room.q.room_number))
        packages = list(BreakfastPackage.selectBy(is_active=True))
        return self._get_context(
            page='guests',
            guest=None,
            rooms=rooms,
            packages=packages,
            errors=None
        )

    @expose()
    @require_login
    def create(self, **kw):
        try:
            name = kw.get('name', '').strip()
            room_id = kw.get('room_id')
            id_card = kw.get('id_card', '').strip()
            phone = kw.get('phone', '').strip()

            if not name or not room_id:
                self._flash('姓名和房间不能为空', 'danger')
                redirect(url('/guests/new'))

            dup_query = Guest.select(AND(
                Guest.q.roomID == int(room_id),
                Guest.q.status == 'checked_in',
                Guest.q.name == name
            ))
            if id_card:
                dup_query = Guest.select(AND(
                    Guest.q.roomID == int(room_id),
                    Guest.q.status == 'checked_in',
                    OR(
                        Guest.q.id_card == id_card,
                        AND(Guest.q.name == name, Guest.q.phone == phone) if phone else Guest.q.name == name
                    )
                ))
            elif phone:
                dup_query = Guest.select(AND(
                    Guest.q.roomID == int(room_id),
                    Guest.q.status == 'checked_in',
                    AND(Guest.q.name == name, Guest.q.phone == phone)
                ))

            if dup_query.count() > 0:
                self._flash('该住客已在此房间登记过，不可重复登记', 'danger')
                redirect(url('/guests/new'))

            check_in = kw.get('check_in_date') or date.today().isoformat()
            check_out = kw.get('check_out_date') or None

            guest = Guest(
                name=name,
                id_card=id_card,
                phone=phone,
                roomID=int(room_id),
                check_in_date=date.fromisoformat(check_in),
                check_out_date=date.fromisoformat(check_out) if check_out else None,
                breakfast_included=kw.get('breakfast_included') == 'on',
                package_typeID=int(kw['package_type_id']) if kw.get('package_type_id') else None,
                status='checked_in',
                notes=kw.get('notes', '')
            )

            room = Room.get(int(room_id))
            room.status = 'occupied'

            self._flash('住客登记成功', 'success')
        except Exception as e:
            self._flash(f'登记失败: {str(e)}', 'danger')
        redirect(url('/guests'))

    @expose('breakfast_management.templates.guests.form')
    @require_login
    def edit(self, id, **kw):
        try:
            guest = Guest.get(int(id))
        except:
            flash('住客不存在', 'danger')
            redirect(url('/guests'))
        rooms = list(Room.select().orderBy(Room.q.room_number))
        packages = list(BreakfastPackage.selectBy(is_active=True))
        return self._get_context(
            page='guests',
            guest=guest,
            rooms=rooms,
            packages=packages,
            errors=None
        )

    @expose()
    @require_login
    def update(self, id, **kw):
        try:
            guest = Guest.get(int(id))

            new_name = kw.get('name', '').strip() if kw.get('name') else guest.name
            new_room_id = int(kw['room_id']) if kw.get('room_id') else guest.roomID
            new_id_card = kw.get('id_card', '').strip() if 'id_card' in kw else guest.id_card
            new_phone = kw.get('phone', '').strip() if 'phone' in kw else guest.phone

            if new_room_id != guest.roomID or new_name != guest.name or new_id_card != guest.id_card or new_phone != guest.phone:
                dup_query = Guest.select(AND(
                    Guest.q.id != int(id),
                    Guest.q.roomID == new_room_id,
                    Guest.q.status == 'checked_in',
                    Guest.q.name == new_name
                ))
                if new_id_card:
                    dup_query = Guest.select(AND(
                        Guest.q.id != int(id),
                        Guest.q.roomID == new_room_id,
                        Guest.q.status == 'checked_in',
                        OR(
                            Guest.q.id_card == new_id_card,
                            AND(Guest.q.name == new_name, Guest.q.phone == new_phone) if new_phone else Guest.q.name == new_name
                        )
                    ))
                elif new_phone:
                    dup_query = Guest.select(AND(
                        Guest.q.id != int(id),
                        Guest.q.roomID == new_room_id,
                        Guest.q.status == 'checked_in',
                        AND(Guest.q.name == new_name, Guest.q.phone == new_phone)
                    ))
                if dup_query.count() > 0:
                    self._flash('该住客已在此房间登记过，不可重复登记', 'danger')
                    redirect(url(f'/guests/{id}/edit'))

            if kw.get('name'):
                guest.name = new_name
            if 'id_card' in kw:
                guest.id_card = new_id_card
            if 'phone' in kw:
                guest.phone = new_phone
            if kw.get('room_id'):
                old_room = guest.room
                if new_room_id != old_room.id:
                    if not Guest.select(AND(Guest.q.roomID == old_room.id, Guest.q.status == 'checked_in', Guest.q.id != int(id))).count():
                        old_room.status = 'vacant'
                    new_room = Room.get(new_room_id)
                    new_room.status = 'occupied'
                guest.roomID = new_room_id
            if kw.get('check_in_date'):
                guest.check_in_date = date.fromisoformat(kw['check_in_date'])
            if kw.get('check_out_date'):
                guest.check_out_date = date.fromisoformat(kw['check_out_date'])
            if 'breakfast_included' in kw:
                guest.breakfast_included = kw.get('breakfast_included') == 'on'
            if kw.get('package_type_id'):
                guest.package_typeID = int(kw['package_type_id'])
            elif 'package_type_id' in kw:
                guest.package_typeID = None
            if kw.get('status'):
                guest.status = kw['status']
                if kw['status'] == 'checked_out':
                    room = guest.room
                    if not Guest.select(AND(Guest.q.roomID == room.id, Guest.q.status == 'checked_in', Guest.q.id != int(id))).count():
                        room.status = 'vacant'
                    if not guest.check_out_date:
                        guest.check_out_date = date.today()
            if 'notes' in kw:
                guest.notes = kw.get('notes', '')
            self._flash('住客信息更新成功', 'success')
        except Exception as e:
            self._flash(f'更新失败: {str(e)}', 'danger')
        redirect(url('/guests'))

    @expose()
    @require_login
    def delete(self, id, **kw):
        try:
            guest = Guest.get(int(id))
            room = guest.room
            guest.destroySelf()
            if not Guest.selectBy(roomID=room.id, status='checked_in').count():
                room.status = 'vacant'
            self._flash('住客记录已删除', 'success')
        except Exception as e:
            self._flash(f'删除失败: {str(e)}', 'danger')
        redirect(url('/guests'))
