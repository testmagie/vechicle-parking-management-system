from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__)  # Corrected to __name__
app.secret_key = os.urandom(24)  # Set a random, secure secret key

# Database Initialization
def init_db():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        # Create parking_slots table
        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS parking_slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slot_number INTEGER UNIQUE NOT NULL,
                vehicle_type TEXT NOT NULL,
                is_occupied INTEGER NOT NULL,  -- Corrected line
                vehicle_number TEXT UNIQUE,
                vehicle_owner TEXT,
                in_time TEXT,
                out_time TEXT,
                payment_status TEXT,
                amount_paid REAL DEFAULT 0,
                penalty_time REAL DEFAULT 0,
                penalty_amount REAL DEFAULT 0
            )
        ''')

        # Add initial slots if not already present
        cursor.execute('SELECT COUNT(*) FROM parking_slots')
        if cursor.fetchone()[0] == 0:
            for i in range(1, 20):  # Create 20 parking slots
                vehicle_type = 'Car' if i <= 10 else 'Bike'  # 10 for Cars, 10 for Bikes
                cursor.execute('INSERT INTO parking_slots (slot_number, vehicle_type, is_occupied) VALUES (?, ?, ?)',
                               (i, vehicle_type, 0))
        conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/slots', methods=['GET', 'POST'])
def show_slots():
    if request.method == 'POST':
        vehicle_type = request.form['vehicle_type']
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT slot_number FROM parking_slots WHERE vehicle_type = ? AND is_occupied = 0''', (vehicle_type,))
            available_slots = cursor.fetchall()

        if not available_slots:
            return render_template('index.html', message=f"No available slots for {vehicle_type}. All slots are booked.")

        # Redirect to the appropriate booking page based on vehicle type
        if vehicle_type == 'Car':
            return redirect(url_for('car_book_slot'))
        elif vehicle_type == 'Bike':
            return redirect(url_for('bike_book_slot'))
    
    return render_template('index.html')

@app.route('/car/book', methods=['GET', 'POST'])
def car_book_slot():
    if request.method == 'POST':
        vehicle_number = request.form['vehicle_number']
        vehicle_owner = request.form['vehicle_owner']
        slot_number = request.form['slot_number']
        in_time = request.form['in_time']
        out_time = request.form['out_time']
        payment_method = request.form['payment_method']
        rate_per_hour = 5

        in_time_dt = datetime.strptime(in_time, '%Y-%m-%dT%H:%M')
        out_time_dt = datetime.strptime(out_time, '%Y-%m-%dT%H:%M')

        duration = (out_time_dt - in_time_dt).total_seconds() / 3600
        amount_paid = int(duration * rate_per_hour)

        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()

            # Check for duplicate vehicle number
            cursor.execute('SELECT vehicle_number, slot_number FROM parking_slots WHERE vehicle_number = ?', (vehicle_number,))
            result = cursor.fetchone()

            # If the vehicle number is already booked, return available slots
            if result:
                cursor.execute('SELECT slot_number FROM parking_slots WHERE vehicle_type = "Car" AND is_occupied = 0')
                available_slots = cursor.fetchall()
                message = "This vehicle number is already booked."
                return render_template('book_car.html', message=message, slots=available_slots, vehicle_number=vehicle_number, vehicle_owner=vehicle_owner, in_time=in_time, out_time=out_time, rate_per_hour=rate_per_hour)

            # Update database with the new booking
            cursor.execute('''
                UPDATE parking_slots SET is_occupied = 1, vehicle_number = ?, vehicle_owner = ?, in_time = ?, 
                out_time = ?, payment_status = ?, amount_paid = ? WHERE slot_number = ?''',
                           (vehicle_number, vehicle_owner, in_time, out_time, payment_method, amount_paid, slot_number))
            conn.commit()

        return render_template('success.html', slot_number=slot_number, amount_paid=amount_paid)
    else:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT slot_number FROM parking_slots WHERE vehicle_type = "Car" AND is_occupied = 0')
            available_slots = cursor.fetchall()
        return render_template('book_car.html', slots=available_slots, rate_per_hour=5)

@app.route('/bike/book', methods=['GET', 'POST'])
def bike_book_slot():
    if request.method == 'POST':
        vehicle_number = request.form['vehicle_number']
        vehicle_owner = request.form['vehicle_owner']
        slot_number = request.form['slot_number']
        in_time = request.form['in_time']
        out_time = request.form['out_time']
        payment_method = request.form['payment_method']
        rate_per_hour = 2

        in_time_dt = datetime.strptime(in_time, '%Y-%m-%dT%H:%M')
        out_time_dt = datetime.strptime(out_time, '%Y-%m-%dT%H:%M')

        duration = (out_time_dt - in_time_dt).total_seconds() / 3600
        amount_paid = int(duration * rate_per_hour)

        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()

            # Check for duplicate vehicle number
            cursor.execute('SELECT vehicle_number, slot_number FROM parking_slots WHERE vehicle_number = ?', (vehicle_number,))
            result = cursor.fetchone()

            # If the vehicle number is already booked, return available slots
            if result:
                cursor.execute('SELECT slot_number FROM parking_slots WHERE vehicle_type = "Bike" AND is_occupied = 0')
                available_slots = cursor.fetchall()
                message = "This vehicle number is already booked."
                return render_template('book_bike.html', message=message, slots=available_slots, vehicle_number=vehicle_number, vehicle_owner=vehicle_owner, in_time=in_time, out_time=out_time, rate_per_hour=rate_per_hour)

            # Update database with the new booking
            cursor.execute('''
                UPDATE parking_slots SET is_occupied = 1, vehicle_number = ?, vehicle_owner = ?, in_time = ?, 
                out_time = ?, payment_status = ?, amount_paid = ? WHERE slot_number = ?''',
                           (vehicle_number, vehicle_owner, in_time, out_time, payment_method, amount_paid, slot_number))
            conn.commit()

        return render_template('success.html', slot_number=slot_number, amount_paid=amount_paid)
    else:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT slot_number FROM parking_slots WHERE vehicle_type = "Bike" AND is_occupied = 0')
            available_slots = cursor.fetchall()
        return render_template('book_bike.html', slots=available_slots, rate_per_hour=2)

@app.route('/status')
def parking_status():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT slot_number, is_occupied, vehicle_number, in_time, out_time FROM parking_slots''')
        slots = cursor.fetchall()
    return render_template('status.html', slots=slots)




@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        vehicle_number = request.form['vehicle_number']
        vehicle_owner = request.form['vehicle_owner']
        
        # Check the database for the vehicle's current out_time and rate_per_hour
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute(''' 
                SELECT out_time, amount_paid, is_occupied, vehicle_type FROM parking_slots 
                WHERE vehicle_number = ? AND vehicle_owner = ?
            ''', (vehicle_number, vehicle_owner))
            result = cursor.fetchone()
        
        if result:
            out_time_str, amount_paid, is_occupied, vehicle_type = result

            # Determine the rate per hour based on vehicle type
            rate_per_hour = 5 if vehicle_type == 'Car' else 2

            # If the slot is occupied
            if is_occupied:
                out_time = datetime.strptime(out_time_str, '%Y-%m-%dT%H:%M')
                current_time = datetime.now()

                # Check if current time is more than 30 minutes after out_time
                if current_time > out_time + timedelta(minutes=30):
                    penalty_time = (current_time - out_time).total_seconds() / 3600  # Penalty time in hours
                    penalty_amount = int(penalty_time * rate_per_hour)
                    
                    # Update penalty details in the database
                    with sqlite3.connect('database.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute(''' 
                            UPDATE parking_slots SET penalty_time = ?, penalty_amount = ? 
                            WHERE vehicle_number = ?
                        ''', (penalty_time, penalty_amount, vehicle_number))
                        conn.commit()

                    # Render penalty payment page
                    return render_template('pay_penalty.html', penalty_time=penalty_time, penalty_amount=penalty_amount, vehicle_number=vehicle_number)

                else:
                    # No penalty, proceed to checkout
                    return redirect(url_for('confirm_checkout', vehicle_number=vehicle_number, vehicle_owner=vehicle_owner))

            else:
                return "This vehicle is not currently parked in the system."

        return render_template('notfound.html')

    
    return render_template('checkout.html')

@app.route('/pay_penalty', methods=['POST'])
def pay_penalty():
    vehicle_number = request.form['vehicle_number']
    penalty_amount = int(request.form['penalty_amount'])
    
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        
        # Mark penalty payment as completed
        cursor.execute(''' 
            UPDATE parking_slots 
            SET payment_status = "Paid", 
                amount_paid = amount_paid + ?, 
                penalty_time = 0, 
                penalty_amount = 0 
            WHERE vehicle_number = ?
        ''', (penalty_amount, vehicle_number))
        conn.commit()
    
    # Redirect to confirm checkout, which clears other fields
    return redirect(url_for('confirm_checkout', vehicle_number=vehicle_number))

@app.route('/confirm_checkout')
def confirm_checkout():
    vehicle_number = request.args.get('vehicle_number')
    
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        
        # Clear all relevant fields and reset the slot
        cursor.execute(''' 
            UPDATE parking_slots 
            SET is_occupied = 0, 
                vehicle_number = NULL, 
                vehicle_owner = NULL, 
                in_time = NULL, 
                out_time = NULL, 
                amount_paid = 0, 
                payment_status = NULL, 
                penalty_time = 0, 
                penalty_amount = 0 
            WHERE vehicle_number = ?
        ''', (vehicle_number,))
        conn.commit()
    
    return render_template('success1.html', message="Checkout successful! Slot is now free.")
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

@app.route('/admin_login', methods=['GET'])
def admin_login_get():
    return render_template('admin_login.html')

@app.route('/admin_login', methods=['POST'])
def admin_login_post():
    username = request.form['username']
    password = request.form['password']
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['logged_in'] = True
        return redirect(url_for('admin_get'))
    else:
        return render_template('admin_login.html', error_message="Incorrect username or password!")
@app.route('/admin', methods=['GET'])
def admin_get():
    if 'logged_in' in session:
        try:
            with sqlite3.connect('database.db') as conn:
                cursor = conn.cursor()
                cursor.execute(''' 
                    SELECT 
                        slot_number, 
                        vehicle_type, 
                        vehicle_number, 
                        vehicle_owner, 
                        in_time, 
                        out_time, 
                        payment_status, 
                        amount_paid, 
                        is_occupied, 
                        penalty_amount 
                    FROM 
                        parking_slots
                ''')
                slots = cursor.fetchall()
            return render_template('admin.html', slots=slots)
        except sqlite3.Error as e:
            print(f"Database error occurred: {e}")
            return "Database error. Please check the logs for details."
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            return "An unexpected error occurred. Please check the logs for details."
    else:
        return redirect(url_for('admin_login_get'))
    
if __name__ == '__main__':
    init_db()  # Initialize database
    app.run(debug=True)
