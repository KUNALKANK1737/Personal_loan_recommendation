import numpy as np
from flask import Flask, request, render_template
import pickle
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

app = Flask(__name__)


load_dotenv()

try:
    with open('model.pkl', 'rb') as file:
        model = pickle.load(file)
    print("Model loaded successfully.")
except FileNotFoundError:
    print("Error: The file 'model.pkl' was not found.")
except Exception as e:
    print(f"Error loading the model: {e}")


def send_email(email, subject, body):
    """
    Send an email notification.

    :param email: Recipient email address
    :param subject: Email subject
    :param body: Email body
    """
    load_dotenv()  

    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')

    if not sender_email or not sender_password:
        raise ValueError("Email address and password must be set in environment variables.")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
      
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
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
    try:
      
        email = request.form.get('email', '')
        int_features = [
            float(request.form.get('loan_id', 0)),
            float(request.form.get('no_of_dependents', 0)),
            float(request.form.get('education', 0)),
            float(request.form.get('self_employed', 0)),
            float(request.form.get('Income', 0.0)),
            float(request.form.get('loan_amount', 0.0)),
            float(request.form.get('loan_term', 0.0)),
            float(request.form.get('cibil_score', 0.0)),
            float(request.form.get('residential_assets_value', 0.0)),
            float(request.form.get('commercial_assets_value', 0.0)),
            float(request.form.get('luxury_assets_value', 0.0)),
            float(request.form.get('bank_asset_value', 0.0))
        ]

        print("Features for prediction:", int_features)

       
        final_features = [np.array(int_features)]

        
        prediction = model.predict(final_features)
        output = prediction[0]

       
        if output == 1:
            result_text = "Congratulations! You are eligible for the loan."
            subject = "Loan Approval"
            body = (
                "Dear Customer,\n\n"
                "We are pleased to inform you that your loan application has been approved.\n"
                "You are eligible for our exclusive home loan products.\n\n"
                "Here are some of our recommended home loan options:\n"
                "- **Home Loan A**: 5% interest rate\n"
                "- **Home Loan B**: 4.5% interest rate\n"
                "- **Home Loan C**: 4.7% interest rate\n\n"
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

        
        return render_template(
            'index.html',
            prediction_text=result_text
        )

    except Exception as e:
        return render_template('index.html', prediction_text=f'Error during prediction: {e}')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
