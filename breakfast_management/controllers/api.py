# -*- coding: utf-8 -*-
from tg import expose, request, redirect, url
from tg.decorators import with_trailing_slash
from breakfast_management.controllers.base import BaseController, require_login, _flash
from breakfast_management.model import (
    DeliveryRecord, Room, Guest, Basket, BreakfastPackage,
    PreparationSchedule
)
from sqlobject import AND, OR
from datetime import date, datetime


class ApiController(BaseController):

    @expose('json')
    @require_login
    def stats(self, **kw):
        stat_date = kw.get('date') or date.today().isoformat()
        d = date.fromisoformat(stat_date)

        slot_counts = {}
        for slot in ['early', 'morning', 'late']:
            slot_counts[slot] = DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == d,
                DeliveryRecord.q.time_slot == slot,
                DeliveryRecord.q.status != 'cancelled'
            )).count()

        package_stats = {}
        deliveries = DeliveryRecord.select(AND(
            DeliveryRecord.q.delivery_date == d,
            DeliveryRecord.q.status != 'cancelled'
        ))
        for dr in deliveries:
            try:
                if dr.basket and dr.basket.package_type:
                    name = dr.basket.package_type.name
                    package_stats[name] = package_stats.get(name, 0) + 1
            except:
                pass

        status_stats = {
            'pending': DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == d,
                DeliveryRecord.q.status == 'pending'
            )).count(),
            'delivering': DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == d,
                DeliveryRecord.q.status == 'delivering'
            )).count(),
            'delivered': DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == d,
                DeliveryRecord.q.status == 'delivered'
            )).count(),
            'returned': DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == d,
                DeliveryRecord.q.status == 'returned'
            )).count(),
        }

        return {
            'date': stat_date,
            'slot_counts': slot_counts,
            'package_stats': package_stats,
            'status_stats': status_stats,
            'total_deliveries': sum(slot_counts.values()),
            'returned_count': status_stats['returned']
        }

    @expose('json')
    @require_login
    def search(self, **kw):
        results = {
            'deliveries': [],
            'baskets': [],
            'guests': [],
            'rooms': []
        }
        keyword = kw.get('q', '').strip()
        if not keyword:
            return results

        try:
            dvs = DeliveryRecord.select(OR(
                DeliveryRecord.q.delivery_no.contains(keyword),
                DeliveryRecord.q.notes.contains(keyword)
            ))[:20]
            for d in dvs:
                results['deliveries'].append({
                    'id': d.id,
                    'delivery_no': d.delivery_no,
                    'room': d.room.room_number if d.room else '',
                    'status': d.status,
                    'date': d.delivery_date.isoformat()
                })
        except:
            pass

        try:
            bks = Basket.select(OR(
                Basket.q.basket_code.contains(keyword),
                Basket.q.notes.contains(keyword)
            ))[:20]
            for b in bks:
                results['baskets'].append({
                    'id': b.id,
                    'basket_code': b.basket_code,
                    'status': b.status,
                    'kitchen': b.kitchen
                })
        except:
            pass

        try:
            gs = Guest.select(OR(
                Guest.q.name.contains(keyword),
                Guest.q.phone.contains(keyword)
            ))[:20]
            for g in gs:
                results['guests'].append({
                    'id': g.id,
                    'name': g.name,
                    'phone': g.phone,
                    'room': g.room.room_number if g.room else '',
                    'status': g.status
                })
        except:
            pass

        try:
            rs = Room.select(Room.q.room_number.contains(keyword))[:20]
            for r in rs:
                results['rooms'].append({
                    'id': r.id,
                    'room_number': r.room_number,
                    'status': r.status,
                    'type': r.room_type
                })
        except:
            pass

        return results
