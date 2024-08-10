from flask import Flask, request, jsonify, send_file
import requests
secret_key = "" # recaptchaのシークレットさいときー
webhook_url = "" #ログチャンネルのウェブフックURL


app = Flask(__name__)

user_ids = {}
@app.route('/')
def index():
    user_id = request.args.get("id")
    if user_id:
        user_ids[str(request.remote_addr)] = str(user_id)
        return send_file('index.html')
    else:
        return jsonify({"error": "ID not provided"}), 400

@app.route('/recaptcha-complete', methods=['POST'])
def recaptcha_complete():
    if request.is_json:
        data = request.get_json()
        recaptcha_response = data.get('recaptcha_token')

        secret_key = secret_key

        verification_response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': secret_key,
                'response': recaptcha_response
            }
        )
        verification_result = verification_response.json()
        print(verification_response.text)

        if verification_result.get('success'):
            requests.post(webhook_url,json={"content":user_ids[str(request.remote_addr)]})
            return jsonify({'message': 'Verification successful'})
        else:
            return jsonify({'message': 'reCAPTCHA verification failed!'}), 400
    else:
        return jsonify({'message': 'Invalid content type'}), 415
    
app.run(host='0.0.0.0', port=7000)
