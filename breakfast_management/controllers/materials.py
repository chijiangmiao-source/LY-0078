# -*- coding: utf-8 -*-
from tg import expose, request, redirect, url, session
from breakfast_management.controllers.base import BaseController, require_login, _flash
from breakfast_management.model import (
    PreparationMaterial, BreakfastPackage, Ingredient,
    PreparationSchedule, User
)
from sqlobject import AND, OR
from datetime import date, datetime


class MaterialsController(BaseController):

    @expose('breakfast_management.templates.materials.index')
    @require_login
    def index(self, **kw):
        query = PreparationMaterial.select()
        if kw.get('prep_date'):
            query = PreparationMaterial.select(
                PreparationMaterial.q.prep_date == date.fromisoformat(kw['prep_date'])
            )
        else:
            query = PreparationMaterial.select(
                PreparationMaterial.q.prep_date == date.today()
            )
        if kw.get('time_slot'):
            query = PreparationMaterial.select(AND(query.expression, PreparationMaterial.q.time_slot == kw['time_slot']))
        if kw.get('status'):
            query = PreparationMaterial.select(AND(query.expression, PreparationMaterial.q.status == kw['status']))
        if kw.get('package_type_id'):
            query = PreparationMaterial.select(AND(query.expression, PreparationMaterial.q.package_typeID == int(kw['package_type_id'])))

        materials = list(query.orderBy(
            PreparationMaterial.q.prep_date,
            PreparationMaterial.q.time_slot,
            PreparationMaterial.q.package_typeID
        ))
        packages = list(BreakfastPackage.selectBy(is_active=True))
        return self._get_context(
            page='materials',
            materials=materials,
            packages=packages,
            filters=kw,
            today=date.today()
        )

    @expose('breakfast_management.templates.materials.form')
    @require_login
    def new(self, **kw):
        packages = list(BreakfastPackage.selectBy(is_active=True))
        ingredients = list(Ingredient.selectBy(is_active=True))
        schedules = list(PreparationSchedule.select(
            PreparationSchedule.q.schedule_date == date.today()
        ).orderBy(PreparationSchedule.q.time_slot))
        return self._get_context(
            page='materials',
            material=None,
            packages=packages,
            ingredients=ingredients,
            schedules=schedules,
            errors=None
        )

    def _validate_schedule(self, schedule_id, prep_date, package_type_id):
        if not schedule_id:
            return None
        try:
            schedule = PreparationSchedule.get(int(schedule_id))
            if schedule.schedule_date != date.fromisoformat(prep_date):
                raise Exception('关联的排期日期与备料日期不一致')
            if schedule.package_typeID != int(package_type_id):
                raise Exception('关联的排期套餐与备料套餐不一致')
            return schedule
        except Exception as e:
            raise

    @expose()
    @require_login
    def create(self, **kw):
        try:
            prep_date = kw.get('prep_date') or date.today().isoformat()
            time_slot = kw.get('time_slot')
            package_type_id = kw.get('package_type_id')
            ingredient_id = kw.get('ingredient_id')
            planned_qty = kw.get('planned_qty', 0)
            schedule_id = kw.get('schedule_id')

            if not time_slot or not package_type_id or not ingredient_id:
                self._flash('请填写时段、套餐和原材料', 'danger')
                redirect(url('/materials/new'))

            if schedule_id:
                try:
                    self._validate_schedule(schedule_id, prep_date, package_type_id)
                except Exception as e:
                    self._flash(f'排期关联校验失败: {str(e)}', 'danger')
                    redirect(url('/materials/new'))

            existing = PreparationMaterial.select(AND(
                PreparationMaterial.q.prep_date == date.fromisoformat(prep_date),
                PreparationMaterial.q.time_slot == time_slot,
                PreparationMaterial.q.package_typeID == int(package_type_id),
                PreparationMaterial.q.ingredientID == int(ingredient_id)
            )).count()
            if existing:
                self._flash('该日期时段套餐的该原材料备料已存在', 'warning')
                redirect(url('/materials'))

            PreparationMaterial(
                prep_date=date.fromisoformat(prep_date),
                time_slot=time_slot,
                package_typeID=int(package_type_id),
                ingredientID=int(ingredient_id),
                scheduleID=int(schedule_id) if schedule_id else None,
                planned_qty=int(planned_qty),
                actual_qty=0,
                status='pending',
                notes=kw.get('notes', '')
            )
            self._flash('备料记录创建成功', 'success')
        except Exception as e:
            self._flash(f'创建失败: {str(e)}', 'danger')
        redirect(url('/materials'))

    @expose('breakfast_management.templates.materials.form')
    @require_login
    def edit(self, id, **kw):
        try:
            material = PreparationMaterial.get(int(id))
        except:
            self._flash('备料记录不存在', 'danger')
            redirect(url('/materials'))
        packages = list(BreakfastPackage.selectBy(is_active=True))
        ingredients = list(Ingredient.selectBy(is_active=True))
        schedules = list(PreparationSchedule.select(
            PreparationSchedule.q.schedule_date == material.prep_date
        ).orderBy(PreparationSchedule.q.time_slot))
        return self._get_context(
            page='materials',
            material=material,
            packages=packages,
            ingredients=ingredients,
            schedules=schedules,
            errors=None
        )

    @expose()
    @require_login
    def update(self, id, **kw):
        try:
            material = PreparationMaterial.get(int(id))
            if material.status == 'completed':
                self._flash('已完成的备料不能修改', 'danger')
                redirect(url('/materials'))

            new_prep_date = kw.get('prep_date', material.prep_date.isoformat())
            new_package_type_id = kw.get('package_type_id', str(material.package_typeID))
            new_schedule_id = kw.get('schedule_id', str(material.scheduleID) if material.scheduleID else '')

            if new_schedule_id:
                try:
                    self._validate_schedule(new_schedule_id, new_prep_date, new_package_type_id)
                except Exception as e:
                    self._flash(f'排期关联校验失败: {str(e)}', 'danger')
                    redirect(url(f'/materials/{id}/edit'))

            action = kw.get('action', '')
            new_status = kw.get('status', material.status)
            new_actual_qty = kw.get('actual_qty')

            will_complete = (action == 'complete') or (new_status == 'completed' and material.status != 'completed')

            if will_complete:
                actual_qty_val = int(new_actual_qty) if new_actual_qty else material.actual_qty
                if actual_qty_val <= 0:
                    self._flash('完成备料前必须填写实际领用量', 'danger')
                    redirect(url(f'/materials/{id}/edit'))

            if kw.get('prep_date'):
                material.prep_date = date.fromisoformat(kw['prep_date'])
            if kw.get('time_slot'):
                material.time_slot = kw['time_slot']
            if kw.get('package_type_id'):
                material.package_typeID = int(kw['package_type_id'])
            if kw.get('ingredient_id'):
                material.ingredientID = int(kw['ingredient_id'])
            if 'schedule_id' in kw:
                material.scheduleID = int(kw['schedule_id']) if kw['schedule_id'] else None
            if kw.get('planned_qty') is not None:
                material.planned_qty = int(kw.get('planned_qty', 0))
            if new_actual_qty is not None:
                material.actual_qty = int(new_actual_qty)
            if will_complete:
                user = self._get_current_user()
                material.status = 'completed'
                material.prepared_byID = user.id if user else None
                material.completed_at = datetime.now()
            elif kw.get('status'):
                material.status = kw['status']
            if 'notes' in kw:
                material.notes = kw.get('notes', '')
            self._flash('备料记录更新成功', 'success')
        except Exception as e:
            self._flash(f'更新失败: {str(e)}', 'danger')
        redirect(url('/materials'))

    @expose()
    @require_login
    def complete(self, id, **kw):
        try:
            material = PreparationMaterial.get(int(id))
            if material.status == 'completed':
                self._flash('备料已完成', 'warning')
            else:
                actual_qty = kw.get('actual_qty')
                if not actual_qty and material.actual_qty == 0:
                    self._flash('请填写实际领用量后再完成备料', 'danger')
                    redirect(url('/materials'))
                    return

                user = self._get_current_user()
                material.status = 'completed'
                material.prepared_byID = user.id if user else None
                material.completed_at = datetime.now()
                if actual_qty:
                    material.actual_qty = int(actual_qty)
                self._flash('备料已完成', 'success')
        except Exception as e:
            self._flash(f'操作失败: {str(e)}', 'danger')
        redirect(url('/materials'))

    @expose()
    @require_login
    def cancel(self, id, **kw):
        try:
            material = PreparationMaterial.get(int(id))
            if material.status == 'completed':
                self._flash('已完成的备料不能取消', 'danger')
            elif material.status == 'cancelled':
                self._flash('备料已取消', 'warning')
            else:
                material.status = 'cancelled'
                self._flash('备料已取消', 'success')
        except Exception as e:
            self._flash(f'取消失败: {str(e)}', 'danger')
        redirect(url('/materials'))

    @expose()
    @require_login
    def delete(self, id, **kw):
        try:
            material = PreparationMaterial.get(int(id))
            if material.status != 'cancelled':
                self._flash('只有已取消的备料记录才能删除，请先取消', 'danger')
            else:
                material.destroySelf()
                self._flash('备料记录已删除', 'success')
        except Exception as e:
            self._flash(f'删除失败: {str(e)}', 'danger')
        redirect(url('/materials'))

    @expose()
    @require_login
    def bulk_create_from_schedules(self, **kw):
        try:
            target_date = kw.get('prep_date') or date.today().isoformat()
            schedules = list(PreparationSchedule.select(
                PreparationSchedule.q.schedule_date == date.fromisoformat(target_date)
            ))
            if not schedules:
                self._flash('指定日期没有备餐排期', 'warning')
                redirect(url('/materials'))

            default_ingredients = list(Ingredient.selectBy(is_active=True))
            created_count = 0
            for s in schedules:
                for ing in default_ingredients:
                    existing = PreparationMaterial.select(AND(
                        PreparationMaterial.q.prep_date == date.fromisoformat(target_date),
                        PreparationMaterial.q.time_slot == s.time_slot,
                        PreparationMaterial.q.package_typeID == s.package_typeID,
                        PreparationMaterial.q.ingredientID == ing.id
                    )).count()
                    if not existing:
                        PreparationMaterial(
                            prep_date=date.fromisoformat(target_date),
                            time_slot=s.time_slot,
                            package_typeID=s.package_typeID,
                            ingredientID=ing.id,
                            scheduleID=s.id,
                            planned_qty=s.quantity,
                            actual_qty=0,
                            status='pending',
                            notes=''
                        )
                        created_count += 1

            self._flash(f'已批量生成 {created_count} 条备料记录', 'success')
        except Exception as e:
            self._flash(f'批量生成失败: {str(e)}', 'danger')
        redirect(url('/materials'))
