from flask import Flask, render_template, request, redirect, flash, url_for, session
from __init__ import app, login, db
import admin
import dao
from flask_login import login_user, logout_user
import json
import urllib.request
import urllib
import requests
import uuid
import hmac
import hashlib
from datetime import datetime
from models import AirportRole, FlightDetails, RoutesInfo, Flight, Routes, Plane, FareClass, Ticket, UserRoleEnum, User, Customer, Seat
from sqlalchemy.exc import IntegrityError


@app.route('/')
def index():
    locations = dao.get_depature_points()
    return render_template('index.html', locations=locations)


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.route("/login", methods=["GET", "POST"])
def login():
    err_msg = ""
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        user = dao.auth_user(email=email, password=password)
        if user:
            login_user(user=user)
            return redirect('/')
        else:
            err_msg = 'Tên đăng nhập hoặc mật khẩu không hợp lệ !'
    return render_template("login.html", err_msg=err_msg)


@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        last_name = request.form.get('lastname')
        first_name = request.form.get('firstname')
        phone = request.form.get('phone')
        address = request.form.get('address')
        email = request.form.get('email')
        password = request.form.get('password')

        if not (last_name and first_name and phone and address and email and password):
            flash('Please fill in all the fields', 'error')
            return redirect(url_for('register'))

        if not dao.check_user_existence(email=email, last_name=last_name, first_name=first_name):
            flash('User already exists. Please choose a different email or username.', 'error')
            return redirect(url_for('register'))
        dao.add_user(last_name=last_name, first_name=first_name, phone=phone, address=address, email=email, password=password)

        flash('User registered successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/ticket/add', methods=["GET", "POST"])
def add_or_update_ticket():
    err = " "
    if request.method == "POST":
        #----- Routes Info
        airport_id = request.form.get('routes_info_airport_id')
        routes_id = request.form.get('routes_info_routes_id')
        airport_role = request.form.get('routes_info_airport_role')

        #----- Flight Details
        flight_id = request.form.get('flight_details_flight_id')
        flight_schedule_id = request.form.get('flight_details_flight_schedule_id')
        time = request.form.get('flight_details_time')
        flight_duration = request.form.get('flight_details_duration', 3.2)
        num_of_seats_1st_class = request.form.get('flight_details_seats_1st_class', 0)
        num_of_seats_2st_class = request.form.get('flight_details_seats_2st_class', 0)

        if airport_role in AirportRole.__members__:
            airport_role = AirportRole[airport_role]



        if dao.add_flight_schedule( airport_id= airport_id,
                                    routes_id=routes_id,
                                    airport_role=airport_role,
                                    flight_id = flight_id,
                                    flight_schedule_id = flight_schedule_id,
                                    time=time,
                                    flight_duration=flight_duration,
                                    num_of_seats_1st_class = num_of_seats_1st_class,
                                    num_of_seats_2st_class = num_of_seats_2st_class):

            return redirect(url_for("ticket"))
        else:
            err = "Something wrong !!!"

    flight_details = FlightDetails.query.get(id)

    return render_template("ticket-add.html",
                           routes=dao.read_routes(),
                           planes=dao.read_planes(),
                           airports=dao.read_airports(),
                           flights=dao.read_flights(),
                           flight_details=dao.get_flight_details_schedule(),
                           flight_schedules = dao.read_flight_schedules(),
                           staffs = dao.read_staffs(),
                           flight = flight_details,
                           err=err)


@app.route('/ticket/update/flight/<int:flight_details_id>', methods=['GET', 'POST'])
def update_ticket_by_id(flight_details_id):

    flight_detail = FlightDetails.query \
        .join(Flight, FlightDetails.flight_id == Flight.id) \
        .join(Routes, Flight.routes_id == Routes.id) \
        .join(RoutesInfo, Routes.id == RoutesInfo.routes_id) \
        .filter(FlightDetails.id == flight_details_id) \
        .first()

    routes_info = RoutesInfo.query.join(FlightDetails, RoutesInfo.routes_id == FlightDetails.id) \
                                  .filter(FlightDetails.id == flight_details_id) \
                                  .first()

    if request.method == 'POST':
            if routes_info:
                # Update routes_info
                routes_info.airport_id = request.form.getlist('routes_info_airport_id')[0]
                routes_info.routes_id = request.form.getlist('routes_info_routes_id')[0]
                routes_info.airport_role = request.form.getlist('routes_info_airport_role')[0]
                db.session.commit()

            if flight_detail:
                # Update flight_detail
                flight_detail.flight_id = request.form.getlist('flight_details_flight_id')[0]
                flight_detail.flight_schedule_id = request.form.getlist('flight_details_flight_schedule_id')[0]
                flight_detail.time = request.form.getlist('flight_details_time')[0]
                flight_detail.flight_duration = request.form.getlist('flight_details_duration')[0]
                flight_detail.num_of_seats_1st_class = request.form.getlist('flight_details_seats_1st_class')[0]
                flight_detail.num_of_seats_2st_class = request.form.getlist('flight_details_seats_2st_class')[0]

                db.session.commit()

            return redirect(url_for('ticket'))

    return render_template("ticket-update.html",
                           routes=dao.read_routes(),
                           planes=dao.read_planes(),
                           airports=dao.read_airports(),
                           flights=dao.read_flights(),
                           flight_details=dao.get_flight_details_schedule(),
                           flight_schedules=dao.read_flight_schedules(),
                           staffs=dao.read_staffs(),
                           flight=flight_detail,
                           routes_info=routes_info)


@app.route('/ticket/delete/<int:flight_details_id>', methods=['GET', 'POST'])
def delete_ticket_by_id(flight_details_id):
        flight_details = FlightDetails.query.filter_by(id=flight_details_id).first()

        if flight_details:
            db.session.delete(flight_details)
            db.session.commit()

            return redirect(url_for('ticket'))


@app.route('/bookticket', methods=['POST'])
def find_ticket():
    departure_airport_id = request.form.get('departure')
    arrival_airport_id = request.form.get('destination')
    departure_date = request.form.get('departure-date')
    return_date = request.form.get('return-date')
    num_of_tickets = request.form.get('quantity-tickets')

    departure_flight_data, arrival_flight_data, ticket_info = dao.get_flight_details(departure_airport_id,
                                                                                     arrival_airport_id,
                                                                                     departure_date,
                                                                                     return_date,
                                                                                     num_of_tickets)
    return render_template("bookticket.html", departure_flight_data=departure_flight_data,
                           arrival_flight_data=arrival_flight_data, ticket_info=ticket_info,
                           num_of_tickets=num_of_tickets)


@app.route(
    '/load_form_passenger/<flight_id>/<plane_id>/<time>/<duration>/<fare_class_id>/<fare_class_price>/<num_of_tickets>')
def load_form_passenger(flight_id, plane_id, time, duration, fare_class_id, fare_class_price, num_of_tickets):
    ticket_info = {
        "flight_id": flight_id,
        "plane_id": plane_id,
        "time": time,
        "duration": duration,
        "fare_class_id": fare_class_id,
        "fare_class_price": fare_class_price,
        "num_of_tickets": num_of_tickets
    }

    session["ticket_info"] = ticket_info
    print(ticket_info)
    return render_template('passenger.html', flight_id=flight_id,
                           plane_id=plane_id, time=time, duration=duration, fare_class_id=fare_class_id,
                           fare_class_price=fare_class_price, num_of_tickets=num_of_tickets)


@app.route('/ticket')
def ticket():
    airport_id = request.args.get("airport_id")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    fli = dao.get_flight_details_schedule(airport_id=airport_id, from_date=from_date, to_date=to_date)
    air = dao.read_airports()

    return render_template("ticket.html",
                           flights=fli, airports=air)


@app.route('/payments', methods=["GET", "POST"])
def payments():
    first_name = request.form.get('first-name')
    last_name = request.form.get('last-name')
    email = request.form.get('email')
    phone_number = request.form.get('phone-number')
    address = request.form.get('address')

    passenger_info = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone_number": phone_number,
        "address": address
    }

    print(passenger_info)

    session["passenger"] = passenger_info

    return render_template('payment.html', session=session)


@app.route('/thanks', methods=["GET"])
def load_thanks_page():
    return render_template("thanks.html")


@app.route('/payUrl', methods=['GET'])
def handle_payments():
    # parameters send to MoMo get get payUrl
    endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
    partnerCode = "MOMO"
    accessKey = "F8BBA842ECF85"
    secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
    orderInfo = "Thanh toan qua MoMo"
    redirectUrl = "http://127.0.0.1:5000/thanks"
    ipnUrl = "http://127.0.0.1:5000/momo_ipn"
    amount = "10000"
    orderId = str(uuid.uuid4())
    requestId = str(uuid.uuid4())
    requestType = "payWithATM"
    extraData = ""  # pass empty value or Encode base64 JsonString
    # before sign HMAC SHA256 with format: accessKey=$accessKey&amount=$amount&extraData=$extraData&ipnUrl=$ipnUrl
    # &orderId=$orderId&orderInfo=$orderInfo&partnerCode=$partnerCode&redirectUrl=$redirectUrl&requestId=$requestId
    # &requestType=$requestType
    rawSignature = "accessKey=" + accessKey + "&amount=" + amount + "&extraData=" + extraData + "&ipnUrl=" + ipnUrl + "&orderId=" + orderId + "&orderInfo=" + orderInfo + "&partnerCode=" + partnerCode + "&redirectUrl=" + redirectUrl + "&requestId=" + requestId + "&requestType=" + requestType

    print(rawSignature)
    # signature
    h = hmac.new(bytes(secretKey, 'ascii'), bytes(rawSignature, 'ascii'), hashlib.sha256)
    signature = h.hexdigest()

    # json object send to MoMo endpoint

    data = {
        'partnerCode': partnerCode,
        'partnerName': "Test",
        'storeId': "MomoTestStore",
        'requestId': requestId,
        'amount': amount,
        'orderId': orderId,
        'orderInfo': orderInfo,
        'redirectUrl': redirectUrl,
        'ipnUrl': ipnUrl,
        'lang': "vi",
        'extraData': extraData,
        'requestType': requestType,
        'signature': signature
    }
    data = json.dumps(data)

    clen = len(data)
    response = requests.post(endpoint, data=data,
                             headers={'Content-Type': 'application/json', 'Content-Length': str(clen)})

    # f.close()
    print("--------------------JSON response----------------\n")
    print(response.json())

    print(response.json()['payUrl'])

    try:
        response = requests.post(endpoint, data=data,
                                 headers={'Content-Type': 'application/json', 'Content-Length': str(clen)})

        # Xử lý phản hồi từ API
        if response.status_code == 200:
            data = response.json()
            user_ino = session.get("passenger")
            dao.add_user(user_ino.get("last_name"),
                         user_ino.get("first_name"),
                         user_ino.get("phone_number"),
                         user_ino.get("address"),
                         user_ino.get("email"))

            return redirect(data.get('payUrl'))
        else:
            return f'Error: {response.status_code}'
    except Exception as e:
        return f'Error: {str(e)}'


#NGUYEN VAN A	9704 0000 0000 0018	03/07	OTP

#BanVe

@app.route('/search-flights')
def flights():
    return render_template('search-flights.html')


@app.route('/flights')
def result():
    f = request.args.get('from')
    t = request.args.get('to')
    departure_date = request.args.get('departure_date')
    return_date = request.args.get('return_date')
    flights = dao.load_flights(f, t, departure_date, return_date)
    return render_template('flights.html', flights=flights, f=f, t=t, departure_date=departure_date,
                           return_date=return_date)


@app.route('/routes/<int:id>')
def routes(id):
    flights = dao.load_flights(route_id=id)
    return render_template('flights.html', flights=flights)


@app.route('/flights/<int:id>')
def flight_details(id):
    flight = Flight.query.get(id)
    flight_details = FlightDetails.query.filter_by(flight_id=id).first()
    plane = Plane.query.get(flight.plane_id)
    route = Routes.query.get(flight.routes_id)
    fare_classes = FareClass.query.all()
    return render_template('flight-details.html', flight=flight, flight_details=flight_details, plane=plane,
                           route=route, fare_classes=fare_classes)


@app.route('/book_ticket/<int:flight_id>', methods=['POST'])
def book_ticket(flight_id):
    client_name = request.form.get('client_name')
    cccd = request.form.get('cccd')
    phone = request.form.get('phone')
    fare_class_id = request.form.get('fare_class')

    # Split client name to first name and last name
    names = client_name.split()
    first_name = names[0]
    last_name = ' '.join(names[1:]) if len(names) > 1 else ''

    # Check for existing user by customer identification or email
    email = f'{cccd}@gmail.com'
    new_user = User.query.filter((User.customer_identification == cccd) | (User.email == email)).first()

    if not new_user:
        # Create a new user
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            address='N/A',
            email=email,
            password=None,
            avatar=None,
            user_role=UserRoleEnum.CUSTOMER,
            joined_date=datetime.now(),
            customer_identification=cccd
        )
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Có lỗi xảy ra khi tạo người dùng mới.', 'error')
            return redirect(url_for('flight_details', id=flight_id))

    # Check for existing customer by user_id
    new_customer = Customer.query.filter_by(user_id=new_user.id).first()
    if not new_customer:
        new_customer = Customer(user_id=new_user.id)
        db.session.add(new_customer)
        db.session.commit()

    # Find the smallest seat ID in the specified fare class that is available for the flight
    booked_seats = db.session.query(Ticket.seat_id).join(Seat).filter(
        Ticket.flight_id == flight_id,
        Seat.fare_class_id == fare_class_id
    ).all()
    booked_seat_ids = [seat.seat_id for seat in booked_seats]

    available_seat = Seat.query.filter(
        Seat.fare_class_id == fare_class_id,
        Seat.plane_id == Flight.query.get(flight_id).plane_id,
        ~Seat.id.in_(booked_seat_ids)
    ).order_by(Seat.id).first()

    if not available_seat:
        flash('Không còn ghế thuộc hạng vé đã chọn.', 'error')
        return redirect(url_for('flight_details', id=flight_id))

    # Create a new ticket
    new_ticket = Ticket(
        flight_id=flight_id,
        fare_class_id=fare_class_id,
        booking_date=datetime.now(),
        customer_id=new_customer.id,
        seat_id=available_seat.id
    )
    db.session.add(new_ticket)
    db.session.commit()

    flash('Đặt vé thành công!', 'success')
    return redirect(url_for('flight_details', id=flight_id))


if __name__ == '__main__':
    with app.app_context():
         app.run(debug = True)