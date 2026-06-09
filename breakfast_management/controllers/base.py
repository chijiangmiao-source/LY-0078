# -*- coding: utf-8 -*-
from tg import TGController, request, session, redirect, url, flash
from breakfast_management.model import User
import hashlib


def require_login(func):
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('请先登录', 'warning')
            redirect(url('/login'))
        try:
            user = User.get(user_id)
            if not user.is_active:
                session.delete()
                flash('账号已被禁用', 'danger')
                redirect(url('/login'))
            request.identity = user
        except:
            session.delete()
            flash('登录状态已过期', 'warning')
            redirect(url('/login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


class BaseController(TGController):
    def __before__(self, *args, **kwargs):
        pass

    def _get_current_user(self):
        user_id = session.get('user_id')
        if user_id:
            try:
                return User.get(user_id)
            except:
                return None
        return None

    def _get_context(self, **extra):
        ctx = {
            'current_user': self._get_current_user(),
            'request': request,
            'session': session,
        }
        ctx.update(extra)
        return ctx
