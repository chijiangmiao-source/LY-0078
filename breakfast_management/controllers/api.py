# -*- coding: utf-8 -*-
from tg import expose, request, redirect, url
from tg.decorators import with_trailing_slash
from breakfast_management.controllers.base import BaseController, require_login, _flash
from breakfast_management.model import (
    DeliveryRecord, Room, Guest, Basket, BreakfastPackage,
    PreparationSchedule, WasteRecord
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

        try:
            signed_count = DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == d,
                DeliveryRecord.q.sign_status == 'signed'
            )).count()
        except Exception:
            signed_count = 0
        try:
            rejected_count = DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == d,
                DeliveryRecord.q.sign_status == 'rejected'
            )).count()
        except Exception:
            rejected_count = 0
        try:
            unsigned_count = DeliveryRecord.select(AND(
                DeliveryRecord.q.delivery_date == d,
                DeliveryRecord.q.sign_status == 'unsigned',
                DeliveryRecord.q.status == 'delivered'
            )).count()
        except Exception:
            unsigned_count = 0

        total_for_sign_rate = signed_count + rejected_count + unsigned_count
        sign_rate = round((signed_count * 100.0 / total_for_sign_rate), 1) if total_for_sign_rate else 0.0

        sign_stats = {
            'signed': signed_count,
            'rejected': rejected_count,
            'unsigned': unsigned_count,
            'sign_rate': sign_rate
        }

        try:
            wastes_today = list(WasteRecord.select(
                WasteRecord.q.waste_date == d
            ))
            waste_quantity = sum(w.quantity for w in wastes_today)
        except Exception:
            wastes_today = []
            waste_quantity = 0

        waste_package_stats = {}
        try:
            for w in wastes_today:
                try:
                    name = w.package_type.name if w.package_type else '未指定'
                except Exception:
                    name = '未指定'
                waste_package_stats[name] = waste_package_stats.get(name, 0) + w.quantity
        except Exception:
            pass

        waste_stats = {
            'total_quantity': waste_quantity,
            'package_stats': waste_package_stats
        }

        return {
            'date': stat_date,
            'slot_counts': slot_counts,
            'package_stats': package_stats,
            'status_stats': status_stats,
            'sign_stats': sign_stats,
            'waste_stats': waste_stats,
            'total_deliveries': sum(slot_counts.values()),
            'returned_count': status_stats['returned'],
            'signed_count': signed_count,
            'sign_rate': sign_rate,
            'waste_quantity': waste_quantity
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
