from flask import Flask, url_for, redirect, render_template, request, abort \
        , Blueprint, flash
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, current_user
from flask_security.utils import encrypt_password
from flask_security.decorators import roles_required
from sqlalchemy.event import listens_for
from sqlalchemy import String, Enum, insert
from flask_admin import Admin, form, expose, BaseView
from flask_admin.form import rules
from flask_admin.contrib import sqla
from flask_admin import helpers as admin_helpers
from flask_admin.base import AdminIndexView
from flask_admin.model import typefmt
from flask_admin.actions import action
from flask_admin.babel import gettext, ngettext, lazy_gettext
from wtforms.fields import IntegerField
import os
import os.path as op
from jinja2 import Markup
import utils_loc
from functools import wraps

app = Flask(__name__, static_folder='files')
#app.register_blueprint(bp, url_prefix='/admin')
app.config.from_pyfile('config.py')
#app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
db = SQLAlchemy(app)



'''
MY_DEFAULT_FORMATTERS = dict(typefmt.BASE_FORMATTERS)
MY_DEFAULT_FORMATTERS.update({
type(None): typefmt.null_formatter,
        price: money_format
    })

'''

# Create directory for file fields to use
file_path = os.path.join(os.path.dirname(__file__), 'files')
try:
    os.mkdir(file_path)
except OSError:
    pass

# Define models
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

def add_card(items_id, qtys, users_id, citys_id):
    #TODO: need write insert in sales
    #connection=db.engine.connect()
    cc_sales = Sales(
            item_id=items_id,
            city_id=citys_id,
            user_id=users_id,
            quantity=qtys
            )
    db.session.add(cc_sales)
    db.session.commit()
    return True



class MyHomeView(AdminIndexView):

    can_edit = False
    can_delete = False
    form_columns = ['quantity', 'items', 'category', 'city']


    @expose('/')
    def index(self):
        return self.render('admin/index.html')


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return self.email


class City(db.Model):
    __tablename__ = 'city'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Unicode(255))

    def __str__(self):
        return self.name

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Unicode(255))

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name



class Items(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Unicode(64))
    #name = db.Column(db.String(50))
    view = db.Column(db.Unicode(128))
    description = db.Column(db.String(255))
    price = db.Column(db.Numeric)
 #TODO: need  read how build custom models with joins
 #   city = db.relationship('City', backref='items')
 #   quantity = db.relationship('Quantity', backref='items')

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return self.name

class Quantity(db.Model):
    __tablename__ = 'quantity'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    #name = db.Column(db.Unicode(64))
    items = db.relationship('Items', backref='quantity')
    city = db.relationship('City', backref='quantity')
    category = db.relationship('Category', backref='quantity')

# db.relationship('Items', backref='Item_name')
    #foreign_keys=item_id)
#TODO: specify relationship
    quantity = db.Column(db.Integer)
    __table_args__ = (
        db.UniqueConstraint("item_id", "city_id"),
    )

    def __int__(self):
        return self.quantity

class Sales(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id =  db.Column(db.Integer, db.ForeignKey('items.id'))
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    quantity = db.Column(db.Integer)
    finished = db.Column(db.Boolean, default=False)
    date = db.Column(db.DATETIME)

    def __str__(self):
        return self.quantity




# Delete hooks for models, delete files if models are getting deleted

@listens_for(Items, 'after_delete')
def del_item(mapper, connection, target):
    if target.view: #after was path
        # Delete image
        try:
            os.remove(op.join(file_path, target.view))
        except OSError:
            pass

        # Delete thumbnail
        try:
            os.remove(op.join(file_path,
                              form.thumbgen_filename(target.view)))
        except OSError:
            pass


#class CityView(sqla.ModelView):





# Flask views

@app.route('/admin/')
@app.route('/admin')
def index():
    return redirect('/')
#    return '<a href="/admin/">Click me to get to Admin!</a>'

#@app.route('/admin')
#@roles_required('admin')

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


class CityView(sqla.ModelView):
    can_edit = True
    can_delete = False
    column_list = ('id','name')
    form_columns = ['name']


class CategoryView(sqla.ModelView):
    can_edit = True
    can_delete = False
    column_list = ('id','name')
    form_columns = ['name']


class SalesView(sqla.ModelView):
    can_edit = True
    can_delete = True

class QuantityView(sqla.ModelView):
    @action('add_card', 'Add_card', 'Are you sure add two card?')
    def action_add(self, ids):
        try:
            query = Quantity.query.filter(Quantity.id.in_(ids))
            count = 0
            for product in query.all():
                if add_card(product.item_id, \
                        1, \
                        current_user.id, \
                        product.city_id):
                    #TODO: place here sql query
                    count += 1
            flash(ngettext('Product added to card',
                           '%(count)s product added',
                           count,
                           count=count))
        except Exception as ex:
                    if not self.handle_view_exception(ex):
                        raise

                    flash(gettext('Failed to add products. %(error)s', error=str(ex)), 'error')





    list_template = 'shop_list.html'
    can_edit = False
    can_delete = False
    form_columns = ['quantity', 'items', 'category', 'city']
    column_filters = ('category', 'city')

'''
form_ajax_refs = {
    'city': QueryAjaxModelLoader('city', db.session, Quantity,
        filters=['city=Paris'])
}

'''

class Warehouse():
    can_edit = False
    can_delete = False
    column_list = ('name', 'city', \
            'quantity', 'price')
#Flask views
class ItemsView(sqla.ModelView):
    def money_format(view, context, model, name):
        return Markup('%s' % model.price)




    def _list_thumbnail(view, context, model, name):
        if not model.view:
            return ''

        return Markup('<img src="%s">' % url_for('static',
                                                 filename=form.thumbgen_filename(model.view)))
    column_formatters = {
        'view': _list_thumbnail,
        'price': money_format
    }

    # Alternative way to contribute field is to override it completely.
    # In this case, Flask-Admin won't attempt to merge various parameters for the field.
    # TODO: add to card options
    form_extra_fields = {
        'view': form.ImageUploadField('Image',
                                      base_path=file_path,
                                      thumbnail_size=(100, 100, True))
    }
    #column_formatters = dict(price='%r' % price)
    form_columns = ['name', 'description', 'price', 'view']
    #if self.has_access():
    #    can_create = False





# Create customized model view class
class SecurityModelView(sqla.ModelView):

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser'):
            return True

        return False

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))




#Create admin
#admin = Admin(app,
#        url = '/',
#        index_view=MyHomeView(),
#        name='Foodtastic',\
#        base_template='my_master.html', \
#        template_mode='bootstrap3')

admin = Admin(app,
        name='Foodtastic',

        index_view=MyHomeView(
            url = '/',
            name='Foodtastic',
       #     endpoint='main',
       #     static_folder='static',
            template='index.html'
            )
        ,
       base_template='my_master.html', \
       template_mode='bootstrap3'
    )


admin.add_view(QuantityView(Quantity, db.session, name='Shop'))
admin.add_view(ItemsView(Items, db.session))
admin.add_view(CityView(City, db.session))
admin.add_view(CategoryView(Category, db.session))
admin.add_view(SalesView(Sales, db.session))
admin.add_view(SecurityModelView(Role, db.session))
admin.add_view(SecurityModelView(User, db.session))


# define a context processor for merging flask-admin's template context into the
# flask-security views.
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )




if __name__ == '__main__':

    # Build a sample db on the fly, if one does not exist yet.
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        utils_loc.build_sample_db(db, app, Role, user_datastore)

    # Start app
    app.run(debug=True)





