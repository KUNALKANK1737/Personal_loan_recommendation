import numpy as np
from flask import Flask, request, render_template
import pickle
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import pandas as pd

# Load environment variables
load_dotenv()

app = Flask(__name__)

eligibility_model = None

def load_model():
    global eligibility_model
    try:
        with open('model.pkl', 'rb') as file:
            eligibility_model = pickle.load(file)
            print(f"Model loaded successfully: {type(eligibility_model)}")
    except FileNotFoundError:
        print("Error: The file 'model.pkl' was not found.")
    except Exception as e:
        print(f"Error loading the model: {e}")

load_model()

loan_products = [
    # List of loan products as in the original code
]

def recommend_loans(user_profile):
    eligible_schemes = [
        product for product in loan_products
        if (product['Min_Income'] <= user_profile['income_annum'] <= product['Max_Income'] and
            product['Min_CIBIL'] <= user_profile['cibil_score'] <= product['Max_CIBIL'] and
            product['Min_Loan_Amount'] <= user_profile['loan_amount'] <= product['Max_Loan_Amount'])
    ]

    if not eligible_schemes:
        return []

    eligible_schemes_df = pd.DataFrame(eligible_schemes)
    eligible_schemes_df['Loan_Amount_Difference'] = eligible_schemes_df.apply(
        lambda row: min(abs(user_profile['loan_amount'] - row['Min_Loan_Amount']),
                        abs(user_profile['loan_amount'] - row['Max_Loan_Amount'])),
        axis=1
    )
    eligible_schemes_df = eligible_schemes_df.sort_values(by=['Loan_Amount_Difference', 'Interest_Rate'])
    return eligible_schemes_df.head(3).to_dict('records')

def send_email(email, subject, body):
    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')

    if not sender_email or not sender_password:
        print("Email address and password must be set in environment variables.")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"Email sent successfully to {email}")
    except smtplib.SMTPAuthenticationError as auth_error:
        print(f"Failed to send email: SMTP Authentication Error - {auth_error}")
    except smtplib.SMTPException as smtp_error:
        print(f"Failed to send email: SMTP Error - {smtp_error}")
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if eligibility_model is None:
        error_message = "The model is not loaded. Please check the logs for more details."
        print(error_message)
        return render_template('result.html', error_message=error_message)

    try:
        email = request.form.get('email', '')
        user_profile = {
            'self_employed': int(request.form.get('self_employed', 0)),
            'income_annum': float(request.form.get('income_annum', 0.0)),
            'loan_amount': float(request.form.get('loan_amount', 0.0)),
            'loan_term': float(request.form.get('loan_term', 0.0)),
            'cibil_score': float(request.form.get('cibil_score', 0.0)),
            'assets': float(request.form.get('assets', 0.0))
        }
        print("User Profile:", user_profile)

        features = np.array([
            user_profile['self_employed'],
            user_profile['income_annum'],
            user_profile['loan_amount'],
            user_profile['loan_term'],
            user_profile['cibil_score'],
            user_profile['assets']
        ]).reshape(1, -1)
        
        prediction = eligibility_model.predict(features)
        output = prediction[0]
        print("Model Prediction:", output)

        if output == 1:
            result_text = "Congratulations! You are eligible for the loan."
            subject = "Loan Approval"

            recommended_schemes = recommend_loans(user_profile)
            print(recommended_schemes)

            if recommended_schemes:
                schemes_list = "\n".join([
                    f"{row['Product_Name']}: {row['Interest_Rate']}% interest rate for {row['Loan_Term_Years']} years."
                    for row in recommended_schemes
                ])
                body = (
                    "Dear Customer,\n\n"
                    "We are pleased to inform you that your loan application has been approved.\n"
                    "Based on your profile, we recommend the following home loan schemes:\n\n"
                    f"{schemes_list}\n\n"
                    "Thank you for choosing our services.\n\n"
                    "Best regards,\nLoan Department"
                )
            else:
                result_text = "Congratulations! You are eligible for the loan, but we could not find suitable schemes based on your profile."
                body = (
                    "Dear Customer,\n\n"
                    "We are pleased to inform you that your loan application has been approved.\n"
                    "However, we could not find any suitable loan schemes based on your profile.\n"
                    "Thank you for choosing our services.\n\n"
                    "Best regards,\nLoan Department"
                )
        else:
            result_text = "Sorry, you are not eligible for the loan."
            subject = "Loan Rejection"
            body = (
                "Dear Customer,\n\n"
                "We regret to inform you that your loan application has been rejected.\n"
                "Please check the eligibility criteria and try again.\n\n"
                "If you have any questions, feel free to contact us.\n\n"
                "Thank you for your interest in our services.\n\n"
                "Best regards,\nLoan Department"
            )

        send_email(email, subject, body)
        
        new_data = {
            'self_employed': [user_profile['self_employed']],
            'income_annum': [user_profile['income_annum']],
            'loan_amount': [user_profile['loan_amount']],
            'loan_term': [user_profile['loan_term']],
            'cibil_score': [user_profile['cibil_score']],
            'assets': [user_profile['assets']],
            'loan_status': [output]
        }
        new_df = pd.DataFrame(new_data)
        new_df.to_csv('customer_data.csv', mode='a', header=False, index=False)

        return render_template('result.html', result_text=result_text, schemes_list=schemes_list)

    except ValueError as e:
        error_message = f"Input error: {e}. Please ensure all inputs are valid numbers."
        print(error_message)
        return render_template('result.html', error_message=error_message)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('result.html', error_message="An error occurred. Please try again.")

if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=8080, debug=True)
    app.run(host='0.0.0.0', port=8080)
