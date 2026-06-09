# -*- coding: utf-8 -*-
from tg import expose, request, redirect, url
from breakfast_management.controllers.base import BaseController, require_login, _flash
from breakfast_management.model import (
    DeliveryRecord, Room, Guest, Basket, BasketAssembly,
    PreparationSchedule, User
)
from sqlobject import AND, OR
from datetime import datetime, date
import uuid


class DeliveriesController(BaseController):

    @expose('breakfast_management.templates.deliveries.index')
    @require_login
    def index(self, **kw):
        query = DeliveryRecord.select()
        if kw.get('keyword'):
            keyword = kw['keyword'].strip()
            query = DeliveryRecord.select(OR(
                DeliveryRecord.q.delivery_no.contains(keyword),
                DeliveryRecord.q.notes.contains(keyword)
            ))
        if kw.get('delivery_date'):
            query = DeliveryRecord.select(AND(
                query.expression,
                DeliveryRecord.q.delivery_date == date.fromisoformat(kw['delivery_date'])
            ))
        else:
            query = DeliveryRecord.select(AND(
                query.expression,
                DeliveryRecord.q.delivery_date == date.today()
            ))
        if kw.get('time_slot'):
            query = DeliveryRecord.select(AND(query.expression, DeliveryRecord.q.time_slot == kw['time_slot']))
        if kw.get('status'):
            query = DeliveryRecord.select(AND(query.expression, DeliveryRecord.q.status == kw['status']))
        if kw.get('room_id'):
            query = DeliveryRecord.select(AND(query.expression, DeliveryRecord.q.roomID == int(kw['room_id'])))

        deliveries = list(query.orderBy(DeliveryRecord.q.created_at))
        rooms = list(Room.select().orderBy(Room.q.room_number))
        return self._get_context(
            page='deliveries',
            deliveries=deliveries,
            rooms=rooms,
            filters=kw,
            today=date.today()
        )

    @expose('breakfast_management.templates.deliveries.form')
    @require_login
    def new(self, **kw):
        today = date.today()
        rooms = list(Room.selectBy(status='occupied').orderBy(Room.q.room_number))
        guests = list(Guest.selectBy(status='checked_in'))
        baskets_in_use = list(Basket.selectBy(status='in_use'))

        available_baskets = []
        for b in baskets_in_use:
            existing = DeliveryRecord.select(AND(
                DeliveryRecord.q.basketID == b.id,
                DeliveryRecord.q.status.in_(['pending', 'delivering', 'delivered'])
            )).count()
            if existing == 0:
                available_baskets.append(b)

        return self._get_context(
            page='deliveries',
            delivery=None,
            rooms=rooms,
            guests=guests,
            baskets=available_baskets,
            errors=None,
            today=today
        )

    @expose()
    @require_login
    def create(self, **kw):
        try:
            room_id = kw.get('room_id')
            basket_id = kw.get('basket_id')
            time_slot = kw.get('time_slot')
            delivery_date = kw.get('delivery_date') or date.today().isoformat()

            if not room_id or not basket_id or not time_slot:
                self._flash('请填写房间、餐篮和配送时段', 'danger')
                redirect(url('/deliveries/new'))

            d_date = date.fromisoformat(delivery_date)
            dup_count = DeliveryRecord.select(AND(
                DeliveryRecord.q.roomID == int(room_id),
                DeliveryRecord.q.delivery_date == d_date,
                DeliveryRecord.q.time_slot == time_slot,
                DeliveryRecord.q.status != 'cancelled'
            )).count()
            if dup_count > 0:
                self._flash('同一房间同一时段不能重复配送', 'danger')
                redirect(url('/deliveries/new'))

            basket = Basket.get(int(basket_id))
            if basket.status != 'in_use':
                self._flash('餐篮状态异常，无法配送', 'danger')
                redirect(url('/deliveries/new'))

            basket_dup = DeliveryRecord.select(AND(
                DeliveryRecord.q.basketID == basket.id,
                DeliveryRecord.q.status.in_(['pending', 'delivering', 'delivered'])
            )).count()
            if basket_dup > 0:
                self._flash('该餐篮已有未完成的配送记录', 'danger')
                redirect(url('/deliveries/new'))

            delivery_no = f'DV{datetime.now().strftime("%Y%m%d%H%M%S")}{uuid.uuid4().hex[:4].upper()}'

            guest_id = None
            if kw.get('guest_id'):
                guest_id = int(kw['guest_id'])

            user = self._get_current_user()

            delivery = DeliveryRecord(
                delivery_no=delivery_no,
                roomID=int(room_id),
                guestID=guest_id,
                basketID=int(basket_id),
                time_slot=time_slot,
                delivery_date=d_date,
                delivery_personID=user.id if user else None,
                status='pending',
                notes=kw.get('notes', '')
            )

            self._flash(f'配送单 {delivery_no} 创建成功', 'success')
        except Exception as e:
            self._flash(f'创建失败: {str(e)}', 'danger')
        redirect(url('/deliveries'))

    @expose()
    @require_login
    def deliver(self, id, **kw):
        try:
            delivery = DeliveryRecord.get(int(id))
            if delivery.status not in ['pending', 'delivering']:
                self._flash('当前状态不能标记送达', 'danger')
                redirect(url('/deliveries'))

            today = date.today()
            schedule = None
            try:
                assemblies = BasketAssembly.selectBy(basketID=delivery.basketID)
                for a in assemblies:
                    if a.schedule:
                        s = a.schedule
                        if s.schedule_date == delivery.delivery_date and s.status == 'completed':
                            schedule = s
                            break
            except:
                pass

            now = datetime.now()
            if schedule and schedule.completed_at:
                if now < schedule.completed_at:
                    self._flash('送达时间不能早于备餐完成时间', 'danger')
                    redirect(url('/deliveries'))

            user = self._get_current_user()
            delivery.status = 'delivered'
            delivery.delivered_at = now
            if not delivery.delivery_personID and user:
                delivery.delivery_personID = user.id
            if not delivery.dispatched_at:
                delivery.dispatched_at = now

            self._flash('配送已标记为送达', 'success')
        except Exception as e:
            self._flash(f'操作失败: {str(e)}', 'danger')
        redirect(url('/deliveries'))

    @expose('breakfast_management.templates.deliveries.return_form')
    @require_login
    def return_basket(self, id, **kw):
        try:
            delivery = DeliveryRecord.get(int(id))
        except:
            self._flash('配送记录不存在', 'danger')
            redirect(url('/deliveries'))

        if request.method == 'POST':
            try:
                if delivery.status not in ['delivered']:
                    self._flash('只有已送达的配送可以退回', 'danger')
                    redirect(url(f'/deliveries/{id}/return'))

                return_time_str = kw.get('returned_at')
                if return_time_str:
                    return_time = datetime.fromisoformat(return_time_str)
                else:
                    return_time = datetime.now()

                if delivery.delivered_at and return_time < delivery.delivered_at:
                    self._flash('退回时间不能早于送达时间', 'danger')
                    redirect(url(f'/deliveries/{id}/return'))

                delivery.status = 'returned'
                delivery.returned_at = return_time
                if 'notes' in kw:
                    delivery.notes = (delivery.notes or '') + '\n' + kw.get('notes', '')

                basket = delivery.basket
                if basket:
                    basket.status = 'cleaning'
                    basket.last_clean_date = date.today()

                self._flash('餐篮已登记退回', 'success')
                redirect(url('/deliveries'))
            except Exception as e:
                self._flash(f'退回失败: {str(e)}', 'danger')
                redirect(url(f'/deliveries/{id}/return'))

        return self._get_context(
            page='deliveries',
            delivery=delivery,
            errors=None
        )

    @expose()
    @require_login
    def delete(self, id, **kw):
        try:
            delivery = DeliveryRecord.get(int(id))
            if delivery.status in ['delivered', 'returned']:
                self._flash('已完成的配送记录不能删除', 'danger')
            else:
                delivery.status = 'cancelled'
                self._flash('配送记录已取消', 'success')
        except Exception as e:
            self._flash(f'操作失败: {str(e)}', 'danger')
        redirect(url('/deliveries'))
