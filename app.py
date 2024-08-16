from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import joblib  
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure key

from pymongo.mongo_client import MongoClient
uri = "mongodb+srv://DATA:<password>@cluster1.aknxsow.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"

client = MongoClient(uri)
db = client['loan_recommendation']
users = db['users']

# Load the ML model
model = joblib.load('model.pkl')

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.example.com'  # Replace with your SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'kankkunal3010@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'Your@Password'  # Replace with your email password
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

def send_email(to, subject, body):
    try:
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[to])
        msg.body = body
        mail.send(msg)
        print(f"Email sent to {to}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Loan products data (unchanged)

# Home Page
@app.route('/')
def home():
    return render_template('home.html')

# Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        if not username or not password or not email:
            return 'All fields are required', 400

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        users.insert_one({'username': username, 'password': hashed_password, 'email': email})
        return redirect(url_for('login'))
    return render_template('signup.html')

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = users.find_one({'username': username})

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['email'] = user['email']
            return redirect(url_for('check_eligibility'))
        else:
            return 'Invalid credentials', 401

    return render_template('login.html')

# Eligibility Check Page
@app.route('/check_eligibility', methods=['GET', 'POST'])
def check_eligibility():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            data = {
                'self_employed': int(request.form['self_employed']),
                'income_annum': float(request.form['income_annum']),
                'loan_amount': float(request.form['loan_amount']),
                'loan_term': float(request.form['loan_term']),
                'cibil_score': float(request.form['cibil_score']),
                'assets': float(request.form['assets'])
            }

            # Prepare input data for model
            input_data = [[data['self_employed'], data['income_annum'], data['loan_amount'],
                           data['loan_term'], data['cibil_score'], data['assets']]]

            # Make prediction
            prediction = model.predict(input_data)[0]

            # Determine eligibility and recommended products
            eligible = prediction == 1
            recommended_products = []

            if eligible:
                for product in loan_products:
                    if (product['Min_CIBIL'] <= data['cibil_score'] <= product['Max_CIBIL'] and
                        product['Min_Loan_Amount'] <= data['loan_amount'] <= product['Max_Loan_Amount'] and
                        product['Min_Income'] <= data['income_annum'] <= product['Max_Income']):
                        recommended_products.append(product)

                if recommended_products:
                    schemes_list = "\n".join([
                        f"{row['Product_Name']}: {row['Interest_Rate']}% interest rate for {row['Loan_Term_Years']} years."
                        for row in recommended_products
                    ])
                    subject = "Loan Approval and Recommendations"
                    body = (
                        "Dear Customer,\n\n"
                        "We are pleased to inform you that your loan application has been approved.\n"
                        "Based on your profile, we recommend the following home loan schemes:\n\n"
                        f"{schemes_list}\n\n"
                        "Thank you for choosing our services.\n\n"
                        "Best regards,\nLoan Department"
                    )
                else:
                    subject = "Loan Approval"
                    body = (
                        "Dear Customer,\n\n"
                        "We are pleased to inform you that your loan application has been approved.\n"
                        "However, we could not find any suitable loan schemes based on your profile.\n"
                        "Thank you for choosing our services.\n\n"
                        "Best regards,\nLoan Department"
                    )
            else:
                subject = "Loan Rejection"
                body = (
                    "Dear Customer,\n\n"
                    "We regret to inform you that your loan application has been rejected.\n"
                    "Please check the eligibility criteria and try again.\n\n"
                    "If you have any questions, feel free to contact us.\n\n"
                    "Thank you for your interest in our services.\n\n"
                    "Best regards,\nLoan Department"
                )

            user_email = session.get('email')
            if user_email:
                send_email(user_email, subject, body)

            return render_template('result.html', eligible=eligible, products=recommended_products)

        except Exception as e:
            return f"An error occurred: {e}", 500

    return render_template('check_eligibility.html')

# Result Page
@app.route('/result')
def result():
    pass  # Consider removing this if unnecessary

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=8080, debug=True)
