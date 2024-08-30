import datetime
import dao
from flask_admin import Admin, BaseView, expose
from flask import request
from __init__ import app, db
from flask_admin.contrib.sqla import ModelView
from models import Flight, Routes, Airport, Plane, User, Ticket, FareClass, Seat, FlightDetails
from wtforms.fields import SelectField
from flask_admin.model.form import InlineFormAdmin

class RoutesView(ModelView):
    column_list = ['id', 'name', 'flights']
    can_export = True
    column_default_sort = ('id', True)
    column_sortable_list = ['id', 'name']
    column_searchable_list = ['id', 'name']
    column_editable_list = ['name']
    column_filters = ['id', 'name']
    column_labels = {
        'id': 'ID',
        'name': 'Tên tuyến bay',
        'flights': 'Các chuyến bay'
    }
    form_excluded_columns = ['airport', 'flights']


class FlightView(ModelView):
    column_list = ['id', 'flight_name', 'routes_id', 'plane_id']
    form_excluded_columns = ['tickets']
    can_export = True
    column_default_sort = ('id', True)
    column_sortable_list = ['id', 'flight_name']
    column_searchable_list = ['id', 'flight_name', 'routes_id']
    column_editable_list = ['flight_name']
    column_filters = ['id', 'flight_name']
    column_labels = {
        'id': 'ID',
        'flight_name': 'Tên chuyến bay',
        'routes_id': 'ID Tuyến bay',
        'plane_id': 'ID Máy bay'
    }


class AirportView(ModelView):
    column_list = ['id', 'name', 'airport_address']
    can_export = True
    column_default_sort = ('id', True)
    column_sortable_list = ['id', 'name', 'airport_address']
    column_searchable_list = ['id', 'name']
    column_editable_list = ['name', 'airport_address']
    column_filters = ['id', 'name']
    column_labels = {
        'id': 'ID',
        'name': 'Tên sân bay',
        'airport_address': 'Địa chỉ sân bay'
    }
    form_excluded_columns = ['routes']


class PlaneView(ModelView):
    column_list = ['id', 'name', 'seats']
    can_export = True
    column_default_sort = ('id', True)
    column_sortable_list = ['id', 'name']
    column_searchable_list = ['id', 'name']
    column_editable_list = ['name']
    column_filters = ['id', 'name']
    column_labels = {
        'id': 'ID',
        'name': 'Tên máy bay'
    }
    form_excluded_columns = ['flight', 'seats']


class UserView(ModelView):
    column_list = ['id', 'first_name', 'last_name', 'email', 'user_role', 'joined_date']
    can_export = True
    column_default_sort = ('id', True)
    column_sortable_list = ['id', 'first_name', 'last_name', 'joined_date']
    column_searchable_list = ['id', 'first_name', 'last_name', 'joined_date']
    column_editable_list = ['first_name']
    column_filters = ['id', 'first_name', 'last_name']
    column_labels = {
        'avatar': 'Ảnh đại diện',
        'id': 'ID',
        'first_name': 'Tên',
        'last_name': 'Họ',
        'email': 'Email',
        'user_role': 'Vai trò',
        'joined_date': "Ngày tham gia"
    }


class FareClassView(ModelView):
    column_list = ['id', 'name', 'price']
    can_export = True
    column_sortable_list = ['id', 'name', 'price']
    column_editable_list = ['name', 'price']
    column_searchable_list = ['id', 'name']
    column_filters = ['id']
    form_excluded_columns = ['seats']
    column_labels = {
        'id': 'ID',
        'name': 'Tên hạng ghế',
        'price': 'Giá tiền'
    }


class SeatView(ModelView):
    column_list = ['id', 'name', 'fare_class_id', 'plane_id']


class TicketView(ModelView):
    column_list = ['id', 'customer_id', 'flight_id', 'fare_class_id', 'booking_date', 'seat_id']
    can_export = True
    column_default_sort = ('booking_date', True)
    column_sortable_list = ['id', 'fare_class_id', 'booking_date']
    column_searchable_list = ['id', 'fare_class_id', 'booking_date']
    column_filters = ['id', 'fare_class_id', 'booking_date']
    column_labels = {
        'id': 'ID',
        'customer_id': 'ID Khách hàng',
        'flight_id': 'ID Chuyến bay',
        'fare_class_id': 'ID Hạng ghế',
        'seat_id': "ID Ghế",
        'booking_date': 'Ngày đặt vé',
    }


class FlightDetailView(ModelView):
    column_list = ['id', 'flight_id', 'flight_duration', 'num_of_seats_1st_class', 'num_of_seats_2st_class',
                   'num_of_empty_seats_1st_class', 'num_of_empty_seats_2st_class']
    can_export = True
    column_sortable_list = ['id', 'flight_duration']
    column_searchable_list = ['id', 'flight_duration']
    column_filters = ['id']
    column_editable_list = ['flight_duration']
    column_labels = {
        'id': 'ID',
        'flight_duration': 'Thời gian bay',
        'flight_id': 'ID Chuyến bay',
        'num_of_seats_1st_class': 'Số lượng ghế hạng 1',
        'num_of_seats_2st_class': "Số lượng ghế hạng 2",
        'num_of_empty_seats_1st_class': 'Số lượng ghế hạng 1 còn trống',
        'num_of_empty_seats_2st_class': 'Số lượng ghế hạng 2 còn trống'
    }


class StatsView(BaseView):
    @expose('/')
    def stats(self):
        # Lấy tham số tháng và năm từ URL
        q = request.args.get('month')
        z = request.args.get('year')

        if q is not None:
            q = int(q)
        if z is not None:
            z = int(z)

        if q is None or z is None:
            # Nếu không có tham số, sử dụng tháng và năm hiện tại
            current_date = datetime.datetime.now()
            q = current_date.month
            z = current_date.year

        num_routes = dao.count_routes()
        total_revenue = sum(dao.revenue_for_month(route_id, q, z) for route_id in range(1, num_routes + 1))
        return self.render('admin/stats.html', dao=dao, num_routes=num_routes, total_revenue=total_revenue, month=q,
                               year=z)


admin = Admin(app, name='ADMIN', template_mode='bootstrap4')
admin.add_view(RoutesView(Routes, db.session, name='Tuyến bay'))
admin.add_view(FlightView(Flight, db.session, name='Chuyến bay'))
admin.add_view(FlightDetailView(FlightDetails, db.session, name='Chi tiết chuyến bay'))
admin.add_view(AirportView(Airport, db.session, name='Sân bay'))
admin.add_view(PlaneView(Plane, db.session, name='Máy bay'))
admin.add_view(FareClassView(FareClass, db.session, name='Hạng ghế'))
admin.add_view(TicketView(Ticket, db.session, name='Vé'))
admin.add_view(UserView(User, db.session, name='Người dùng'))
admin.add_view(StatsView(name='Thống kê'))
