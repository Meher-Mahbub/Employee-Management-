from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key' 

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
ITEMS_PER_PAGE = 10

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@app.route('/page/<int:page>')
def show_employees(page=1):
    conn = get_db_connection()

    search_name = request.args.get('search_name', '')
    search_dob = request.args.get('search_dob', '')
    search_email = request.args.get('search_email', '')
    search_mobile = request.args.get('search_mobile', '')

    query = 'SELECT * FROM employees WHERE 1=1'
    params = []

    if search_name:
        query += ' AND (first_name LIKE ? OR last_name LIKE ?)'
        params.extend([f'%{search_name}%', f'%{search_name}%'])
    if search_dob:
        query += ' AND dob LIKE ?'
        params.append(f'%{search_dob}%')
    if search_email:
        query += ' AND email LIKE ?'
        params.append(f'%{search_email}%')
    if search_mobile:
        query += ' AND mobile LIKE ?'
        params.append(f'%{search_mobile}%')
    
    query += ' LIMIT ? OFFSET ?'
    params.extend([ITEMS_PER_PAGE, (page - 1) * ITEMS_PER_PAGE])

    employees = conn.execute(query, params).fetchall()
    total_employees = conn.execute('SELECT COUNT(*) AS count FROM employees').fetchone()['count']
    conn.close()
    
    total_pages = (total_employees + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    return render_template('index.html', employees=employees, page=page, total_pages=total_pages)

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        mobile = request.form['mobile']
        dob = request.form['dob']
        photo = request.files.get('photo')
        
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(UPLOAD_FOLDER, filename))
        else:
            filename = None
        
        conn = get_db_connection()
        conn.execute('INSERT INTO employees (first_name, last_name, email, mobile, dob, photo) VALUES (?, ?, ?, ?, ?, ?)',
                     (first_name, last_name, email, mobile, dob, filename))
        conn.commit()
        conn.close()
        flash('Employee added successfully!')
        return redirect(url_for('show_employees'))
    
    return render_template('add_employee.html')

@app.route('/edit_employee/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    conn = get_db_connection()
    employee = conn.execute('SELECT * FROM employees WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        mobile = request.form['mobile']
        dob = request.form['dob']
        photo = request.files.get('photo')
        
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(UPLOAD_FOLDER, filename))
        else:
            filename = employee['photo']
        
        conn.execute('UPDATE employees SET first_name = ?, last_name = ?, email = ?, mobile = ?, dob = ?, photo = ? WHERE id = ?',
                     (first_name, last_name, email, mobile, dob, filename, id))
        conn.commit()
        conn.close()
        flash('Employee updated successfully!')
        return redirect(url_for('show_employees'))
    
    return render_template('edit_employee.html', employee=employee)

@app.route('/delete_employee/<int:id>', methods=['POST'])
def delete_employee(id):
    conn = get_db_connection()
    employee = conn.execute('SELECT photo FROM employees WHERE id = ?', (id,)).fetchone()
    
    if employee is None:
        flash('Employee not found!')
        conn.close()
        return redirect(url_for('show_employees'))
    
    conn.execute('DELETE FROM employees WHERE id = ?', (id,))
    conn.commit()
    
    file_path = os.path.join(UPLOAD_FOLDER, employee['photo']) if employee['photo'] else None
    
    if file_path and os.path.isfile(file_path):
        os.remove(file_path)
    else:
        print(f"File not found or no photo to delete: {file_path}")
    
    conn.close()
    flash('Employee deleted successfully!')
    return redirect(url_for('show_employees'))

if __name__ == '__main__':
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            mobile TEXT NOT NULL,
            dob TEXT NOT NULL,
            photo TEXT)
    ''')
    
    conn.execute("INSERT INTO employees (first_name, last_name, email, mobile, dob, photo) VALUES (?, ?, ?, ?, ?, ?)", 
                 ('Abul', 'Kalam', 'Abul@example.com', '1234567890', '1980-01-01', None))
    
    conn.execute("INSERT INTO employees (first_name, last_name, email, mobile, dob, photo) VALUES (?, ?, ?, ?, ?, ?)", 
                 ('Tanim', 'Shahriar', 'tanim.shahriar@example.com', '0987654321', '1990-05-15', None))
    
    conn.commit()
    conn.close()
    
    app.run(debug=True)
