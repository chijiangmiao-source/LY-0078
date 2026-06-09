# -*- coding: utf-8 -*-
from tg import TGController, request, session, redirect, url
from breakfast_management.model import User


def _flash(message, category='info'):
    messages = session.get('_flash_messages', [])
    messages.append({'message': message, 'category': category})
    session['_flash_messages'] = messages
    session.save()


def _get_flash():
    messages = session.get('_flash_messages', [])
    if messages:
        session['_flash_messages'] = []
        try:
            session.save()
        except:
            pass
    return messages


def require_login(func):
    def wrapper(self, *args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            _flash('请先登录', 'warning')
            redirect(url('/login'))
        try:
            user = User.get(user_id)
            if not user.is_active:
                session.delete()
                _flash('账号已被禁用', 'danger')
                redirect(url('/login'))
            request.identity = user
        except Exception:
            session.delete()
            _flash('登录状态已过期', 'warning')
            redirect(url('/login'))
        return func(self, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


class BaseController(TGController):
    def __before__(self, *args, **kwargs):
        pass

    def _flash(self, message, category='info'):
        _flash(message, category)

    def _get_current_user(self):
        user_id = session.get('user_id')
        if user_id:
            try:
                return User.get(user_id)
            except Exception:
                return None
        return None

    def _get_context(self, **extra):
        ctx = {
            'current_user': self._get_current_user(),
            'request': request,
            'session': session,
            'flash_messages': _get_flash(),
        }
        ctx.update(extra)
        return ctx
