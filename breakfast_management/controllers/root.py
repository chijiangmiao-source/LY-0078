# -*- coding: utf-8 -*-
from tg import expose, request, session, redirect, url
from breakfast_management.controllers.base import BaseController, require_login, _flash, _get_flash
from breakfast_management.model import (
    User, Room, Guest, BreakfastPackage, Basket,
    PreparationSchedule, BasketAssembly, DeliveryRecord
)
from breakfast_management.controllers.rooms import RoomsController
from breakfast_management.controllers.guests import GuestsController
from breakfast_management.controllers.packages import PackagesController
from breakfast_management.controllers.baskets import BasketsController
from breakfast_management.controllers.schedules import SchedulesController
from breakfast_management.controllers.assembly import AssemblyController
from breakfast_management.controllers.deliveries import DeliveriesController
from breakfast_management.controllers.materials import MaterialsController
from breakfast_management.controllers.api import ApiController
from breakfast_management.lib.security import verify_password
from breakfast_management.model import PreparationMaterial
from datetime import date, datetime
from sqlobject import AND, OR


class RootController(BaseController):
    rooms = RoomsController()
    guests = GuestsController()
    packages = PackagesController()
    baskets = BasketsController()
    schedules = SchedulesController()
    assembly = AssemblyController()
    deliveries = DeliveriesController()
    materials = MaterialsController()
    api = ApiController()

    @expose('breakfast_management.templates.login')
    def login(self, **kw):
        if request.method == 'POST':
            username = kw.get('username', '').strip()
            password = kw.get('password', '')
            if not username or not password:
                self._flash('请输入用户名和密码', 'danger')
                return dict(page='login', error='请输入用户名和密码', flash_messages=_get_flash())
            try:
                user = User.selectBy(username=username).getOne()
                if verify_password(password, user.password) and user.is_active:
                    session['user_id'] = user.id
                    session['username'] = user.username
                    session['role'] = user.role
                    session.save()
                    self._flash('欢迎回来，' + (user.real_name or user.username), 'success')
                    redirect(url('/dashboard'))
                else:
                    self._flash('用户名或密码错误', 'danger')
            except Exception:
                self._flash('用户名或密码错误', 'danger')
        return dict(page='login', error=None, flash_messages=_get_flash())

    @expose()
    def logout(self):
        session.delete()
        session['_flash_messages'] = [{'message': '已退出登录', 'category': 'info'}]
        session.save()
        redirect(url('/login'))

    @expose('breakfast_management.templates.login')
    def index(self, **kw):
        if not session.get('user_id'):
            return self.login(**kw)
        redirect(url('/dashboard'))

    @expose('breakfast_management.templates.dashboard')
    @require_login
    def dashboard(self, **kw):
        today = date.today()

        slot_counts = {}
        for slot in ['early', 'morning', 'late']:
            try:
                cnt = DeliveryRecord.select(AND(
                    DeliveryRecord.q.delivery_date == today,
                    DeliveryRecord.q.time_slot == slot,
                    DeliveryRecord.q.status != 'cancelled'
                )).count()
            except Exception:
                cnt = 0
            slot_counts[slot] = cnt

        package_stats = {}
        try:
            deliveries_today = DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == today,
                DeliveryRecord.q.status != 'cancelled'
            ))
            for d in deliveries_today:
                try:
                    pkg_name = d.basket.package_type.name if d.basket and d.basket.package_type else '未指定'
                except Exception:
                    pkg_name = '未指定'
                package_stats[pkg_name] = package_stats.get(pkg_name, 0) + 1
        except Exception:
            pass

        try:
            returned_count = DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == today,
                DeliveryRecord.q.status == 'returned'
            )).count()
        except Exception:
            returned_count = 0

        try:
            pending_count = DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == today,
                DeliveryRecord.q.status == 'pending'
            )).count()
        except Exception:
            pending_count = 0

        try:
            delivering_count = DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == today,
                DeliveryRecord.q.status == 'delivering'
            )).count()
        except Exception:
            delivering_count = 0

        try:
            delivered_count = DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == today,
                DeliveryRecord.q.status == 'delivered'
            )).count()
        except Exception:
            delivered_count = 0

        try:
            signed_count = DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == today,
                DeliveryRecord.q.sign_status == 'signed'
            )).count()
        except Exception:
            signed_count = 0

        try:
            rejected_count = DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == today,
                DeliveryRecord.q.sign_status == 'rejected'
            )).count()
        except Exception:
            rejected_count = 0

        try:
            unsigned_count = DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == today,
                DeliveryRecord.q.sign_status == 'unsigned',
                DeliveryRecord.q.status == 'delivered'
            )).count()
        except Exception:
            unsigned_count = 0

        total_for_sign_rate = signed_count + rejected_count + unsigned_count
        sign_rate = round((signed_count * 100.0 / total_for_sign_rate), 1) if total_for_sign_rate else 0.0

        try:
            total_rooms = Room.select().count()
        except Exception:
            total_rooms = 0
        try:
            occupied_rooms = Room.selectBy(status='occupied').count()
        except Exception:
            occupied_rooms = 0
        try:
            active_baskets = Basket.selectBy(status='available').count()
        except Exception:
            active_baskets = 0
        try:
            total_baskets = Basket.select().count()
        except Exception:
            total_baskets = 0

        try:
            pending_materials = PreparationMaterial.select(AND(
                PreparationMaterial.q.prep_date == today,
                PreparationMaterial.q.status == 'pending'
            )).count()
        except Exception:
            pending_materials = 0

        try:
            preparing_materials = PreparationMaterial.select(AND(
                PreparationMaterial.q.prep_date == today,
                PreparationMaterial.q.status == 'preparing'
            )).count()
        except Exception:
            preparing_materials = 0

        try:
            completed_materials = PreparationMaterial.select(AND(
                PreparationMaterial.q.prep_date == today,
                PreparationMaterial.q.status == 'completed'
            )).count()
        except Exception:
            completed_materials = 0

        try:
            total_materials = PreparationMaterial.select(
                PreparationMaterial.q.prep_date == today
            ).count()
        except Exception:
            total_materials = 0

        total_slot_count = sum(slot_counts.values())
        package_total = sum(package_stats.values())
        slot_widths = {
            'early': (slot_counts.get('early', 0) * 100.0 / total_slot_count) if total_slot_count else 0,
            'morning': (slot_counts.get('morning', 0) * 100.0 / total_slot_count) if total_slot_count else 0,
            'late': (slot_counts.get('late', 0) * 100.0 / total_slot_count) if total_slot_count else 0,
        }
        package_stats_list = []
        for pkg_name, cnt in sorted(package_stats.items(), key=lambda x: -x[1]):
            percent = round(cnt * 100.0 / package_total, 1) if package_total else 0
            package_stats_list.append((pkg_name, cnt, percent))

        return self._get_context(
            page='dashboard',
            slot_counts=slot_counts,
            slot_widths=slot_widths,
            package_stats=package_stats,
            package_stats_list=package_stats_list,
            returned_count=returned_count,
            pending_count=pending_count,
            delivering_count=delivering_count,
            delivered_count=delivered_count,
            signed_count=signed_count,
            rejected_count=rejected_count,
            unsigned_count=unsigned_count,
            sign_rate=sign_rate,
            total_rooms=total_rooms,
            occupied_rooms=occupied_rooms,
            active_baskets=active_baskets,
            total_baskets=total_baskets,
            pending_materials=pending_materials,
            preparing_materials=preparing_materials,
            completed_materials=completed_materials,
            total_materials=total_materials,
            today=today
        )
