# -*- coding: utf-8 -*-
from tg import expose, request, session, redirect, url, flash, validate
from tg.decorators import with_trailing_slash
from breakfast_management.controllers.base import BaseController, require_login
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
from breakfast_management.controllers.api import ApiController
from datetime import date, datetime
from sqlobject import AND, OR, func
import hashlib


class RootController(BaseController):
    rooms = RoomsController()
    guests = GuestsController()
    packages = PackagesController()
    baskets = BasketsController()
    schedules = SchedulesController()
    assembly = AssemblyController()
    deliveries = DeliveriesController()
    api = ApiController()

    @expose('breakfast_management.templates.login')
    def login(self, **kw):
        if request.method == 'POST':
            username = kw.get('username', '').strip()
            password = kw.get('password', '')
            if not username or not password:
                flash('请输入用户名和密码', 'danger')
                return dict(page='login', error='请输入用户名和密码')
            try:
                user = User.selectBy(username=username).getOne()
                pwd_hash = hashlib.md5(password.encode()).hexdigest()
                if user.password == pwd_hash and user.is_active:
                    session['user_id'] = user.id
                    session['username'] = user.username
                    session['role'] = user.role
                    session.save()
                    flash(f'欢迎回来，{user.real_name or user.username}', 'success')
                    redirect(url('/dashboard'))
                else:
                    flash('用户名或密码错误', 'danger')
            except:
                flash('用户名或密码错误', 'danger')
        return dict(page='login', error=None)

    @expose()
    def logout(self):
        session.delete()
        flash('已退出登录', 'info')
        redirect(url('/login'))

    @expose('breakfast_management.templates.index')
    @require_login
    def index(self):
        redirect(url('/dashboard'))

    @expose('breakfast_management.templates.dashboard')
    @require_login
    def dashboard(self, **kw):
        today = date.today()

        slot_counts = {}
        for slot in ['early', 'morning', 'late']:
            cnt = DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == today,
                DeliveryRecord.q.time_slot == slot,
                DeliveryRecord.q.status != 'cancelled'
            )).count()
            slot_counts[slot] = cnt

        package_stats = {}
        deliveries_today = DeliveryRecord.select(AND(
            DeliveryRecord.q.delivery_date == today,
            DeliveryRecord.q.status != 'cancelled'
        ))
        for d in deliveries_today:
            try:
                pkg_name = d.basket.package_type.name if d.basket and d.basket.package_type else '未指定'
            except:
                pkg_name = '未指定'
            package_stats[pkg_name] = package_stats.get(pkg_name, 0) + 1

        returned_count = DeliveryRecord.select(AND(
            DeliveryRecord.q.delivery_date == today,
            DeliveryRecord.q.status == 'returned'
        )).count()

        pending_count = DeliveryRecord.select(AND(
            DeliveryRecord.q.delivery_date == today,
            DeliveryRecord.q.status == 'pending'
        )).count()

        delivering_count = DeliveryRecord.select(AND(
            DeliveryRecord.q.delivery_date == today,
            DeliveryRecord.q.status == 'delivering'
        )).count()

        delivered_count = DeliveryRecord.select(AND(
            DeliveryRecord.q.delivery_date == today,
            DeliveryRecord.q.status == 'delivered'
        )).count()

        total_rooms = Room.select().count()
        occupied_rooms = Room.selectBy(status='occupied').count()
        active_baskets = Basket.selectBy(status='available').count()
        total_baskets = Basket.select().count()

        return self._get_context(
            page='dashboard',
            slot_counts=slot_counts,
            package_stats=package_stats,
            returned_count=returned_count,
            pending_count=pending_count,
            delivering_count=delivering_count,
            delivered_count=delivered_count,
            total_rooms=total_rooms,
            occupied_rooms=occupied_rooms,
            active_baskets=active_baskets,
            total_baskets=total_baskets,
            today=today
        )
