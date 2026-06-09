# -*- coding: utf-8 -*-
from datetime import datetime, date


def format_datetime(dt):
    if not dt:
        return ''
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)


def format_date(d):
    if not d:
        return ''
    if isinstance(d, date):
        return d.strftime('%Y-%m-%d')
    return str(d)


def basket_status_label(status):
    labels = {
        'available': '<span class="badge bg-success">可用</span>',
        'in_use': '<span class="badge bg-primary">使用中</span>',
        'cleaning': '<span class="badge bg-warning">清洗中</span>',
        'disabled': '<span class="badge bg-danger">停用</span>',
    }
    return labels.get(status, '<span class="badge bg-secondary">未知</span>')


def delivery_status_label(status):
    labels = {
        'pending': '<span class="badge bg-secondary">待配送</span>',
        'delivering': '<span class="badge bg-primary">配送中</span>',
        'delivered': '<span class="badge bg-success">已送达</span>',
        'returned': '<span class="badge bg-info">已退回</span>',
        'cancelled': '<span class="badge bg-danger">已取消</span>',
    }
    return labels.get(status, '<span class="badge bg-secondary">未知</span>')


def time_slot_label(slot):
    slots = {
        'early': '早段 (6:00-7:00)',
        'morning': '中段 (7:00-8:00)',
        'late': '晚段 (8:00-9:00)',
    }
    return slots.get(slot, slot)
