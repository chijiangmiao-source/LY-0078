# -*- coding: utf-8 -*-
from tg import expose, request, redirect, url
from breakfast_management.controllers.base import BaseController, require_login, _flash
from breakfast_management.model import Room
from sqlobject import AND, OR


class RoomsController(BaseController):

    @expose('breakfast_management.templates.rooms.index')
    @require_login
    def index(self, **kw):
        query = Room.select()
        if kw.get('keyword'):
            keyword = kw['keyword'].strip()
            query = Room.select(OR(
                Room.q.room_number.contains(keyword),
                Room.q.notes.contains(keyword)
            ))
        if kw.get('status'):
            query = Room.select(AND(query.expression, Room.q.status == kw['status']))
        if kw.get('room_type'):
            query = Room.select(AND(query.expression, Room.q.room_type == kw['room_type']))

        rooms = list(query.orderBy(Room.q.room_number))
        return self._get_context(
            page='rooms',
            rooms=rooms,
            filters=kw
        )

    @expose('breakfast_management.templates.rooms.form')
    @require_login
    def new(self, **kw):
        return self._get_context(page='rooms', room=None, errors=None)

    @expose()
    @require_login
    def create(self, **kw):
        try:
            room_number = kw.get('room_number', '').strip()
            if not room_number:
                self._flash('房间号不能为空', 'danger')
                redirect(url('/rooms/new'))
            if Room.selectBy(room_number=room_number).count():
                self._flash('房间号已存在', 'danger')
                redirect(url('/rooms/new'))

            Room(
                room_number=room_number,
                room_type=kw.get('room_type', 'double'),
                floor=int(kw.get('floor', 1)),
                status=kw.get('status', 'vacant'),
                notes=kw.get('notes', '')
            )
            self._flash('房间创建成功', 'success')
        except Exception as e:
            self._flash(f'创建失败: {str(e)}', 'danger')
        redirect(url('/rooms'))

    @expose('breakfast_management.templates.rooms.form')
    @require_login
    def edit(self, id, **kw):
        try:
            room = Room.get(int(id))
        except:
            self._flash('房间不存在', 'danger')
            redirect(url('/rooms'))
        return self._get_context(page='rooms', room=room, errors=None)

    @expose()
    @require_login
    def update(self, id, **kw):
        try:
            room = Room.get(int(id))
            room_number = kw.get('room_number', '').strip()
            if room_number and room_number != room.room_number:
                if Room.selectBy(room_number=room_number).count():
                    self._flash('房间号已存在', 'danger')
                    redirect(url(f'/rooms/{id}/edit'))
                room.room_number = room_number
            if kw.get('room_type'):
                room.room_type = kw['room_type']
            if kw.get('floor'):
                room.floor = int(kw['floor'])
            if kw.get('status'):
                room.status = kw['status']
            if 'notes' in kw:
                room.notes = kw.get('notes', '')
            self._flash('房间更新成功', 'success')
        except Exception as e:
            self._flash(f'更新失败: {str(e)}', 'danger')
        redirect(url('/rooms'))

    @expose()
    @require_login
    def delete(self, id, **kw):
        try:
            room = Room.get(int(id))
            room.destroySelf()
            self._flash('房间已删除', 'success')
        except Exception as e:
            self._flash(f'删除失败: {str(e)}', 'danger')
        redirect(url('/rooms'))
