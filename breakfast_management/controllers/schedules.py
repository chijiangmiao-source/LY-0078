# -*- coding: utf-8 -*-
from tg import expose, request, redirect, url, flash, session
from breakfast_management.controllers.base import BaseController, require_login
from breakfast_management.model import PreparationSchedule, BreakfastPackage, User
from sqlobject import AND, OR
from datetime import date, datetime


class SchedulesController(BaseController):

    @expose('breakfast_management.templates.schedules.index')
    @require_login
    def index(self, **kw):
        query = PreparationSchedule.select()
        if kw.get('schedule_date'):
            query = PreparationSchedule.select(
                PreparationSchedule.q.schedule_date == date.fromisoformat(kw['schedule_date'])
            )
        else:
            query = PreparationSchedule.select(
                PreparationSchedule.q.schedule_date == date.today()
            )
        if kw.get('time_slot'):
            query = PreparationSchedule.select(AND(query.expression, PreparationSchedule.q.time_slot == kw['time_slot']))
        if kw.get('status'):
            query = PreparationSchedule.select(AND(query.expression, PreparationSchedule.q.status == kw['status']))
        if kw.get('package_type_id'):
            query = PreparationSchedule.select(AND(query.expression, PreparationSchedule.q.package_typeID == int(kw['package_type_id'])))

        schedules = list(query.orderBy(PreparationSchedule.q.schedule_date, PreparationSchedule.q.time_slot))
        packages = list(BreakfastPackage.selectBy(is_active=True))
        return self._get_context(
            page='schedules',
            schedules=schedules,
            packages=packages,
            filters=kw,
            today=date.today()
        )

    @expose('breakfast_management.templates.schedules.form')
    @require_login
    def new(self, **kw):
        packages = list(BreakfastPackage.selectBy(is_active=True))
        return self._get_context(page='schedules', schedule=None, packages=packages, errors=None)

    @expose()
    @require_login
    def create(self, **kw):
        try:
            schedule_date = kw.get('schedule_date') or date.today().isoformat()
            time_slot = kw.get('time_slot')
            package_type_id = kw.get('package_type_id')
            quantity = kw.get('quantity', 0)

            if not time_slot or not package_type_id:
                flash('请填写时段和套餐', 'danger')
                redirect(url('/schedules/new'))

            existing = PreparationSchedule.select(AND(
                PreparationSchedule.q.schedule_date == date.fromisoformat(schedule_date),
                PreparationSchedule.q.time_slot == time_slot,
                PreparationSchedule.q.package_typeID == int(package_type_id)
            )).count()
            if existing:
                flash('该时段该套餐的排期已存在', 'warning')
                redirect(url('/schedules'))

            PreparationSchedule(
                schedule_date=date.fromisoformat(schedule_date),
                time_slot=time_slot,
                package_typeID=int(package_type_id),
                quantity=int(quantity),
                status='pending',
                notes=kw.get('notes', '')
            )
            flash('备餐排期创建成功', 'success')
        except Exception as e:
            flash(f'创建失败: {str(e)}', 'danger')
        redirect(url('/schedules'))

    @expose('breakfast_management.templates.schedules.form')
    @require_login
    def edit(self, id, **kw):
        try:
            schedule = PreparationSchedule.get(int(id))
        except:
            flash('排期不存在', 'danger')
            redirect(url('/schedules'))
        packages = list(BreakfastPackage.selectBy(is_active=True))
        return self._get_context(page='schedules', schedule=schedule, packages=packages, errors=None)

    @expose()
    @require_login
    def update(self, id, **kw):
        try:
            schedule = PreparationSchedule.get(int(id))
            if schedule.status == 'completed':
                flash('已完成的排期不能修改', 'danger')
                redirect(url('/schedules'))

            if kw.get('schedule_date'):
                schedule.schedule_date = date.fromisoformat(kw['schedule_date'])
            if kw.get('time_slot'):
                schedule.time_slot = kw['time_slot']
            if kw.get('package_type_id'):
                schedule.package_typeID = int(kw['package_type_id'])
            if kw.get('quantity'):
                schedule.quantity = int(kw['quantity'])
            if kw.get('status'):
                schedule.status = kw['status']
            if 'notes' in kw:
                schedule.notes = kw.get('notes', '')
            flash('排期更新成功', 'success')
        except Exception as e:
            flash(f'更新失败: {str(e)}', 'danger')
        redirect(url('/schedules'))

    @expose()
    @require_login
    def complete(self, id, **kw):
        try:
            schedule = PreparationSchedule.get(int(id))
            if schedule.status == 'completed':
                flash('排期已完成', 'warning')
            else:
                user = self._get_current_user()
                schedule.status = 'completed'
                schedule.prepared_byID = user.id if user else None
                schedule.completed_at = datetime.now()
                flash('备餐已完成', 'success')
        except Exception as e:
            flash(f'操作失败: {str(e)}', 'danger')
        redirect(url('/schedules'))

    @expose()
    @require_login
    def delete(self, id, **kw):
        try:
            schedule = PreparationSchedule.get(int(id))
            if schedule.status == 'completed':
                flash('已完成的排期不能删除', 'danger')
            else:
                schedule.destroySelf()
                flash('排期已删除', 'success')
        except Exception as e:
            flash(f'删除失败: {str(e)}', 'danger')
        redirect(url('/schedules'))
