# -*- coding: utf-8 -*-
from tg import expose, request, redirect, url
from breakfast_management.controllers.base import BaseController, require_login, _flash
from breakfast_management.model import BasketAssembly, Basket, PreparationSchedule, DeliveryRecord
from sqlobject import AND
from datetime import datetime, date


class AssemblyController(BaseController):

    @expose('breakfast_management.templates.assembly.index')
    @require_login
    def index(self, **kw):
        today = date.today()
        schedules = list(PreparationSchedule.select(AND(
            PreparationSchedule.q.schedule_date == today,
            PreparationSchedule.q.status != 'completed'
        )).orderBy(PreparationSchedule.q.time_slot))

        completed_schedules = list(PreparationSchedule.select(AND(
            PreparationSchedule.q.schedule_date == today,
            PreparationSchedule.q.status == 'completed'
        )))

        available_baskets = list(Basket.selectBy(status='available'))
        disabled_baskets = list(Basket.selectBy(status='disabled'))

        assemblies = list(BasketAssembly.select().orderBy(BasketAssembly.q.assembled_at))
        assemblies_today = [a for a in assemblies if a.assembled_at.date() == today]

        return self._get_context(
            page='assembly',
            schedules=schedules,
            completed_schedules=completed_schedules,
            available_baskets=available_baskets,
            disabled_baskets=disabled_baskets,
            assemblies=assemblies_today,
            today=today
        )

    @expose()
    @require_login
    def create(self, **kw):
        try:
            basket_id = kw.get('basket_id')
            schedule_id = kw.get('schedule_id')

            if not basket_id or not schedule_id:
                self._flash('请选择餐篮和排期', 'danger')
                redirect(url('/assembly'))

            basket = Basket.get(int(basket_id))
            schedule = PreparationSchedule.get(int(schedule_id))

            if basket.status == 'disabled':
                self._flash('停用餐篮不能参与装配', 'danger')
                redirect(url('/assembly'))

            if basket.status != 'available':
                self._flash('该餐篮当前不可用', 'danger')
                redirect(url('/assembly'))

            if basket.package_type and basket.package_type.id != schedule.package_type.id:
                self._flash(f'餐篮套餐类型({basket.package_type.name})与排期套餐({schedule.package_type.name})不匹配', 'danger')
                redirect(url('/assembly'))

            if schedule.status != 'completed':
                self._flash('排期尚未备餐完成，不能装配', 'danger')
                redirect(url('/assembly'))

            user = self._get_current_user()
            BasketAssembly(
                basketID=basket.id,
                scheduleID=schedule.id,
                assembled_byID=user.id if user else None,
                assembled_at=datetime.now(),
                status='assembled'
            )

            basket.status = 'in_use'

            self._flash(f'餐篮 {basket.basket_code} 装配成功', 'success')
        except Exception as e:
            self._flash(f'装配失败: {str(e)}', 'danger')
        redirect(url('/assembly'))
