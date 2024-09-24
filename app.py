from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import joblib
import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from flask_mail import Mail, Message
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') 



# Database connection

client = MongoClient(os.getenv('MONGO_URI'))


try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client['loanrecommendation']
users = db['users']

# Load the ML model
model = joblib.load('model.pkl')

def send_email(to_email, subject, body):
    sender_email = os.getenv('EMAIL')
    app_password = os.getenv('EMAIL_PASSWORD')  

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
        
# Loan products
loan_products = [
    {
        "Product_Name": "SBI Premium Home Loan",
        "Min_Income": 500000,
        "Max_Income": 2000000,
        "Min_CIBIL": 800,
        "Max_CIBIL": 900,
        "Min_Loan_Amount": 5000000,
        "Max_Loan_Amount": 50000000,
        "Interest_Rate": 7.5,
        "Loan_Term_Years": 30
    },
    {
        "Product_Name": "SBI Flexipay Home Loan",
        "Min_Income": 300000,
        "Max_Income": 1500000,
        "Min_CIBIL": 750,
        "Max_CIBIL": 850,
        "Min_Loan_Amount": 2000000,
        "Max_Loan_Amount": 20000000,
        "Interest_Rate": 8.0,
        "Loan_Term_Years": 20
    },
    {
        "Product_Name": "SBI Regular Home Loan",
        "Min_Income": 400000,
        "Max_Income": 1800000,
        "Min_CIBIL": 700,
        "Max_CIBIL": 850,
        "Min_Loan_Amount": 1000000,
        "Max_Loan_Amount": 10000000,
        "Interest_Rate": 7.8,
        "Loan_Term_Years": 25
    },
    {
        "Product_Name": "SBI Realty Home Loan",
        "Min_Income": 600000,
        "Max_Income": 2500000,
        "Min_CIBIL": 780,
        "Max_CIBIL": 900,
        "Min_Loan_Amount": 3000000,
        "Max_Loan_Amount": 30000000,
        "Interest_Rate": 7.2,
        "Loan_Term_Years": 35
    },
    {
        "Product_Name": "SBI Tribal Plus Home Loan",
        "Min_Income": 200000,
        "Max_Income": 1200000,
        "Min_CIBIL": 700,
        "Max_CIBIL": 800,
        "Min_Loan_Amount": 1000000,
        "Max_Loan_Amount": 5000000,
        "Interest_Rate": 8.5,
        "Loan_Term_Years": 15
    },
    {
        "Product_Name": "SBI Top-up Home Loan",
        "Min_Income": 400000,
        "Max_Income": 2000000,
        "Min_CIBIL": 700,
        "Max_CIBIL": 850,
        "Min_Loan_Amount": 500000,
        "Max_Loan_Amount": 5000000,
        "Interest_Rate": 8.2,
        "Loan_Term_Years": 10
    },
    {
        "Product_Name": "SBI Earnest Money Deposit Home Loan",
        "Min_Income": 300000,
        "Max_Income": 1000000,
        "Min_CIBIL": 700,
        "Max_CIBIL": 850,
        "Min_Loan_Amount": 500000,
        "Max_Loan_Amount": 3000000,
        "Interest_Rate": 8.5,
        "Loan_Term_Years": 5
    },
    {
        "Product_Name": "SBI CRE Home Loan",
        "Min_Income": 800000,
        "Max_Income": 5000000,
        "Min_CIBIL": 750,
        "Max_CIBIL": 900,
        "Min_Loan_Amount": 10000000,
        "Max_Loan_Amount": 100000000,
        "Interest_Rate": 7.0,
        "Loan_Term_Years": 15
    },
    {
        "Product_Name": "SBI Loan Against Property",
        "Min_Income": 500000,
        "Max_Income": 2500000,
        "Min_CIBIL": 700,
        "Max_CIBIL": 850,
        "Min_Loan_Amount": 2000000,
        "Max_Loan_Amount": 20000000,
        "Interest_Rate": 8.0,
        "Loan_Term_Years": 20
    },
    {
        "Product_Name": "SBI Low Income Home Loan",
        "Min_Income": 150000,
        "Max_Income": 800000,
        "Min_CIBIL": 700,
        "Max_CIBIL": 800,
        "Min_Loan_Amount": 500000,
        "Max_Loan_Amount": 2000000,
        "Interest_Rate": 8.7,
        "Loan_Term_Years": 10
    }
]

# Home Page
@app.route('/')
def home():
    return render_template('home.html')

# Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['username'] 
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

     
        users.insert_one({'username': username, 'password': hashed_password,'email':email})
        return redirect(url_for('login'))
    return render_template('signup.html')

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.find_one({'username': username})

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['email'] = user['username']
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

        user_email = session.get('username')
        
        if user_email:
            send_email(user_email, subject, body)
        
        return render_template('result.html', eligible=eligible, products=recommended_products)

    return render_template('check_eligibility.html')

# Result Page
@app.route('/result')
def result():
    pass  

if __name__ == '__main__':
   app.run(host="0.0.0.0", port = 8080)
   #app.run(host="0.0.0.0",port=8080)
