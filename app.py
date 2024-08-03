import numpy as np
from flask import Flask, request, render_template
import pickle

app = Flask(__name__)


try:
    with open('model.pkl', 'rb') as file:
        model = pickle.load(file)
    print("Model loaded successfully.")
except FileNotFoundError:
    print("Error: The file 'model.pkl' was not found.")
except Exception as e:
    print(f"Error loading the model: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        
        int_features = [
            request.form.get('loan_id', ''),
            request.form.get('no_of_dependents', 0),
            request.form.get('education', ''),
            request.form.get('self_employed', ''),
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

        return render_template('index.html', prediction_text=f'Prediction: {output}')

    except Exception as e:
        return render_template('index.html', prediction_text=f'Error during prediction: {e}')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
