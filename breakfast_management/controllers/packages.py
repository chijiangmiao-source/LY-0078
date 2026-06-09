# -*- coding: utf-8 -*-
from tg import expose, request, redirect, url
from breakfast_management.controllers.base import BaseController, require_login, _flash
from breakfast_management.model import BreakfastPackage
from sqlobject import AND, OR


class PackagesController(BaseController):

    @expose('breakfast_management.templates.packages.index')
    @require_login
    def index(self, **kw):
        query = BreakfastPackage.select()
        if kw.get('keyword'):
            keyword = kw['keyword'].strip()
            query = BreakfastPackage.select(OR(
                BreakfastPackage.q.name.contains(keyword),
                BreakfastPackage.q.code.contains(keyword),
                BreakfastPackage.q.description.contains(keyword)
            ))
        if kw.get('is_active'):
            active = kw['is_active'] == 'true'
            query = BreakfastPackage.select(AND(query.expression, BreakfastPackage.q.is_active == active))

        packages = list(query.orderBy(BreakfastPackage.q.code))
        return self._get_context(
            page='packages',
            packages=packages,
            filters=kw
        )

    @expose('breakfast_management.templates.packages.form')
    @require_login
    def new(self, **kw):
        return self._get_context(page='packages', package=None, errors=None)

    @expose()
    @require_login
    def create(self, **kw):
        try:
            name = kw.get('name', '').strip()
            code = kw.get('code', '').strip()
            if not name or not code:
                self._flash('套餐名称和编号不能为空', 'danger')
                redirect(url('/packages/new'))
            if BreakfastPackage.selectBy(code=code).count():
                self._flash('套餐编号已存在', 'danger')
                redirect(url('/packages/new'))
            if BreakfastPackage.selectBy(name=name).count():
                self._flash('套餐名称已存在', 'danger')
                redirect(url('/packages/new'))

            BreakfastPackage(
                name=name,
                code=code,
                description=kw.get('description', ''),
                price=int(kw.get('price', 0)),
                items=kw.get('items', ''),
                is_active=kw.get('is_active') == 'on'
            )
            self._flash('早餐套餐创建成功', 'success')
        except Exception as e:
            self._flash(f'创建失败: {str(e)}', 'danger')
        redirect(url('/packages'))

    @expose('breakfast_management.templates.packages.form')
    @require_login
    def edit(self, id, **kw):
        try:
            package = BreakfastPackage.get(int(id))
        except:
            self._flash('套餐不存在', 'danger')
            redirect(url('/packages'))
        return self._get_context(page='packages', package=package, errors=None)

    @expose()
    @require_login
    def update(self, id, **kw):
        try:
            package = BreakfastPackage.get(int(id))
            name = kw.get('name', '').strip()
            code = kw.get('code', '').strip()

            if code and code != package.code:
                if BreakfastPackage.selectBy(code=code).count():
                    self._flash('套餐编号已存在', 'danger')
                    redirect(url(f'/packages/{id}/edit'))
                package.code = code
            if name and name != package.name:
                if BreakfastPackage.selectBy(name=name).count():
                    self._flash('套餐名称已存在', 'danger')
                    redirect(url(f'/packages/{id}/edit'))
                package.name = name

            if 'description' in kw:
                package.description = kw.get('description', '')
            if kw.get('price'):
                package.price = int(kw['price'])
            if 'items' in kw:
                package.items = kw.get('items', '')
            if 'is_active' in kw:
                package.is_active = kw.get('is_active') == 'on'

            self._flash('套餐更新成功', 'success')
        except Exception as e:
            self._flash(f'更新失败: {str(e)}', 'danger')
        redirect(url('/packages'))

    @expose()
    @require_login
    def delete(self, id, **kw):
        try:
            package = BreakfastPackage.get(int(id))
            package.is_active = False
            self._flash('套餐已停用', 'success')
        except Exception as e:
            self._flash(f'操作失败: {str(e)}', 'danger')
        redirect(url('/packages'))
