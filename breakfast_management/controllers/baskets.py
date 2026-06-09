# -*- coding: utf-8 -*-
from tg import expose, request, redirect, url
from breakfast_management.controllers.base import BaseController, require_login, _flash
from breakfast_management.model import Basket, BreakfastPackage
from sqlobject import AND, OR
from datetime import date


class BasketsController(BaseController):

    @expose('breakfast_management.templates.baskets.index')
    @require_login
    def index(self, **kw):
        query = Basket.select()
        if kw.get('keyword'):
            keyword = kw['keyword'].strip()
            query = Basket.select(OR(
                Basket.q.basket_code.contains(keyword),
                Basket.q.notes.contains(keyword)
            ))
        if kw.get('status'):
            query = Basket.select(AND(query.expression, Basket.q.status == kw['status']))
        if kw.get('kitchen'):
            query = Basket.select(AND(query.expression, Basket.q.kitchen == kw['kitchen']))
        if kw.get('package_type_id'):
            query = Basket.select(AND(query.expression, Basket.q.package_typeID == int(kw['package_type_id'])))

        baskets = list(query.orderBy(Basket.q.basket_code))
        packages = list(BreakfastPackage.selectBy(is_active=True))
        return self._get_context(
            page='baskets',
            baskets=baskets,
            packages=packages,
            filters=kw
        )

    @expose('breakfast_management.templates.baskets.form')
    @require_login
    def new(self, **kw):
        packages = list(BreakfastPackage.selectBy(is_active=True))
        return self._get_context(page='baskets', basket=None, packages=packages, errors=None)

    @expose()
    @require_login
    def create(self, **kw):
        try:
            basket_code = kw.get('basket_code', '').strip()
            if not basket_code:
                self._flash('餐篮编号不能为空', 'danger')
                redirect(url('/baskets/new'))
            if Basket.selectBy(basket_code=basket_code).count():
                self._flash('餐篮编号已存在，不能重复', 'danger')
                redirect(url('/baskets/new'))

            last_clean = kw.get('last_clean_date') or date.today().isoformat()

            Basket(
                basket_code=basket_code,
                package_typeID=int(kw['package_type_id']) if kw.get('package_type_id') else None,
                kitchen=kw.get('kitchen', 'kitchen_a'),
                status=kw.get('status', 'available'),
                last_clean_date=date.fromisoformat(last_clean),
                notes=kw.get('notes', '')
            )
            self._flash('餐篮创建成功', 'success')
        except Exception as e:
            self._flash(f'创建失败: {str(e)}', 'danger')
        redirect(url('/baskets'))

    @expose('breakfast_management.templates.baskets.form')
    @require_login
    def edit(self, id, **kw):
        try:
            basket = Basket.get(int(id))
        except:
            self._flash('餐篮不存在', 'danger')
            redirect(url('/baskets'))
        packages = list(BreakfastPackage.selectBy(is_active=True))
        return self._get_context(page='baskets', basket=basket, packages=packages, errors=None)

    @expose()
    @require_login
    def update(self, id, **kw):
        try:
            basket = Basket.get(int(id))
            basket_code = kw.get('basket_code', '').strip()

            if basket_code and basket_code != basket.basket_code:
                if Basket.selectBy(basket_code=basket_code).count():
                    self._flash('餐篮编号已存在，不能重复', 'danger')
                    redirect(url(f'/baskets/{id}/edit'))
                basket.basket_code = basket_code

            if kw.get('package_type_id'):
                basket.package_typeID = int(kw['package_type_id'])
            elif 'package_type_id' in kw:
                basket.package_typeID = None

            if kw.get('kitchen'):
                basket.kitchen = kw['kitchen']
            if kw.get('status'):
                basket.status = kw['status']
            if kw.get('last_clean_date'):
                basket.last_clean_date = date.fromisoformat(kw['last_clean_date'])
            if 'notes' in kw:
                basket.notes = kw.get('notes', '')

            self._flash('餐篮更新成功', 'success')
        except Exception as e:
            self._flash(f'更新失败: {str(e)}', 'danger')
        redirect(url('/baskets'))

    @expose()
    @require_login
    def delete(self, id, **kw):
        try:
            basket = Basket.get(int(id))
            if basket.status == 'in_use':
                self._flash('使用中的餐篮不能删除', 'danger')
            else:
                basket.status = 'disabled'
                self._flash('餐篮已停用', 'success')
        except Exception as e:
            self._flash(f'操作失败: {str(e)}', 'danger')
        redirect(url('/baskets'))
