# -*- coding: utf-8 -*-
from tg import expose, request, redirect, url
from breakfast_management.controllers.base import BaseController, require_login, _flash
from breakfast_management.model import (
    WasteRecord, BreakfastPackage, PreparationSchedule,
    PreparationMaterial, DeliveryRecord
)
from sqlobject import AND
from datetime import date, datetime


STAGE_OPTIONS = [
    ('preparation', '备餐'),
    ('assembly', '装配'),
    ('delivery', '配送'),
    ('return', '退回'),
]

REASON_OPTIONS = [
    '过期变质',
    '烹饪失误',
    '装配损坏',
    '配送遗失',
    '客人拒收',
    '退回损耗',
    '备料过量',
    '其他',
]


class WastesController(BaseController):

    @expose('breakfast_management.templates.wastes.index')
    @require_login
    def index(self, **kw):
        query = WasteRecord.select()
        if kw.get('waste_date'):
            query = WasteRecord.select(AND(
                query.expression,
                WasteRecord.q.waste_date == date.fromisoformat(kw['waste_date'])
            ))
        else:
            query = WasteRecord.select(AND(
                query.expression,
                WasteRecord.q.waste_date == date.today()
            ))
        if kw.get('time_slot'):
            query = WasteRecord.select(AND(query.expression, WasteRecord.q.time_slot == kw['time_slot']))
        if kw.get('package_type_id'):
            query = WasteRecord.select(AND(query.expression, WasteRecord.q.package_typeID == int(kw['package_type_id'])))
        if kw.get('stage'):
            query = WasteRecord.select(AND(query.expression, WasteRecord.q.stage == kw['stage']))
        if kw.get('reason'):
            query = WasteRecord.select(AND(query.expression, WasteRecord.q.reason.contains(kw['reason'].strip())))

        wastes = list(query.orderBy(WasteRecord.q.created_at))
        packages = list(BreakfastPackage.selectBy(is_active=True))
        total_quantity = sum(w.quantity for w in wastes)

        return self._get_context(
            page='wastes',
            wastes=wastes,
            packages=packages,
            filters=kw,
            today=date.today(),
            stage_options=STAGE_OPTIONS,
            reason_options=REASON_OPTIONS,
            total_quantity=total_quantity
        )

    @expose('breakfast_management.templates.wastes.form')
    @require_login
    def new(self, **kw):
        packages = list(BreakfastPackage.selectBy(is_active=True))
        schedules = list(PreparationSchedule.select(
            PreparationSchedule.q.schedule_date == date.today()
        ).orderBy(PreparationSchedule.q.time_slot))
        materials = list(PreparationMaterial.select(
            PreparationMaterial.q.prep_date == date.today()
        ))
        deliveries = list(DeliveryRecord.select(
            DeliveryRecord.q.delivery_date == date.today()
        ))

        return self._get_context(
            page='wastes',
            waste=None,
            packages=packages,
            schedules=schedules,
            materials=materials,
            deliveries=deliveries,
            stage_options=STAGE_OPTIONS,
            reason_options=REASON_OPTIONS,
            errors=None,
            today=date.today()
        )

    @expose()
    @require_login
    def create(self, **kw):
        try:
            waste_date = kw.get('waste_date') or date.today().isoformat()
            time_slot = kw.get('time_slot')
            package_type_id = kw.get('package_type_id')
            stage = kw.get('stage', 'preparation')
            quantity = kw.get('quantity', 0)
            reason = kw.get('reason', '').strip()
            schedule_id = kw.get('schedule_id')
            material_id = kw.get('material_id')
            delivery_id = kw.get('delivery_id')

            if not time_slot or not package_type_id:
                self._flash('请填写时段和套餐类型', 'danger')
                redirect(url('/wastes/new'))

            if int(quantity) <= 0:
                self._flash('损耗数量必须大于0', 'danger')
                redirect(url('/wastes/new'))

            if not reason:
                self._flash('请填写损耗原因', 'danger')
                redirect(url('/wastes/new'))

            user = self._get_current_user()

            WasteRecord(
                waste_date=date.fromisoformat(waste_date),
                time_slot=time_slot,
                package_typeID=int(package_type_id),
                stage=stage,
                quantity=int(quantity),
                reason=reason,
                registered_byID=user.id if user else None,
                scheduleID=int(schedule_id) if schedule_id else None,
                materialID=int(material_id) if material_id else None,
                deliveryID=int(delivery_id) if delivery_id else None,
                notes=kw.get('notes', '')
            )
            self._flash('损耗登记成功', 'success')
        except Exception as e:
            self._flash(f'登记失败: {str(e)}', 'danger')
            redirect(url('/wastes/new'))
        redirect(url('/wastes'))

    @expose('breakfast_management.templates.wastes.form')
    @require_login
    def edit(self, id, **kw):
        try:
            waste = WasteRecord.get(int(id))
        except:
            self._flash('损耗记录不存在', 'danger')
            redirect(url('/wastes'))

        packages = list(BreakfastPackage.selectBy(is_active=True))
        schedules = list(PreparationSchedule.select(
            PreparationSchedule.q.schedule_date == waste.waste_date
        ).orderBy(PreparationSchedule.q.time_slot))
        materials = list(PreparationMaterial.select(
            PreparationMaterial.q.prep_date == waste.waste_date
        ))
        deliveries = list(DeliveryRecord.select(
            DeliveryRecord.q.delivery_date == waste.waste_date
        ))

        return self._get_context(
            page='wastes',
            waste=waste,
            packages=packages,
            schedules=schedules,
            materials=materials,
            deliveries=deliveries,
            stage_options=STAGE_OPTIONS,
            reason_options=REASON_OPTIONS,
            errors=None,
            today=date.today()
        )

    @expose()
    @require_login
    def update(self, id, **kw):
        try:
            waste = WasteRecord.get(int(id))

            if kw.get('waste_date'):
                waste.waste_date = date.fromisoformat(kw['waste_date'])
            if kw.get('time_slot'):
                waste.time_slot = kw['time_slot']
            if kw.get('package_type_id'):
                waste.package_typeID = int(kw['package_type_id'])
            if kw.get('stage'):
                waste.stage = kw['stage']
            if kw.get('quantity') is not None:
                if int(kw['quantity']) <= 0:
                    self._flash('损耗数量必须大于0', 'danger')
                    redirect(url(f'/wastes/{id}/edit'))
                waste.quantity = int(kw['quantity'])
            if kw.get('reason') is not None:
                if not kw['reason'].strip():
                    self._flash('请填写损耗原因', 'danger')
                    redirect(url(f'/wastes/{id}/edit'))
                waste.reason = kw['reason'].strip()
            if 'schedule_id' in kw:
                waste.scheduleID = int(kw['schedule_id']) if kw['schedule_id'] else None
            if 'material_id' in kw:
                waste.materialID = int(kw['material_id']) if kw['material_id'] else None
            if 'delivery_id' in kw:
                waste.deliveryID = int(kw['delivery_id']) if kw['delivery_id'] else None
            if 'notes' in kw:
                waste.notes = kw.get('notes', '')

            self._flash('损耗记录更新成功', 'success')
        except Exception as e:
            self._flash(f'更新失败: {str(e)}', 'danger')
        redirect(url('/wastes'))

    @expose()
    @require_login
    def delete(self, id, **kw):
        try:
            waste = WasteRecord.get(int(id))
            waste.destroySelf()
            self._flash('损耗记录已删除', 'success')
        except Exception as e:
            self._flash(f'删除失败: {str(e)}', 'danger')
        redirect(url('/wastes'))
