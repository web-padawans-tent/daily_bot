import json
import time
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify
from functions import generate_merchant_signature, extract_user_id_from_reference, add_user_to_channel, \
    generate_signature, delete_user_from_channel
from loader import MERCHANT_ACCOUNT, MERCHANT_DOMAIN

app = Flask(__name__)


@app.route('/add_user')
async def add_user():
    await add_user_to_channel(7559268811, 'Test')
    return "200"


@app.route('/delete')
async def delete():
    await delete_user_from_channel(7559268811)
    return "200"


@app.route('/')
def index():
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kosovska</title>
<style>
* {
margin: 0;
padding: 0;
box-sizing: border-box;
}

body {
display: flex;
justify-content: center;
align-items: center;
height: 100vh;
background-color: #ffffff;
font-family: Arial, sans-serif;
}

.container {
display: flex;
width: 90%;
max-width: 600px;
flex-direction: column;
align-items: center;
gap: 20px;
background-color: #eeeeee;
padding: 40px;
border-radius: 10px;
box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.btn {
width: 100%;
display: inline-block;
padding: 15px 15px;
border-radius: 50px;
border: 1px solid #050505;
text-decoration: none;
text-align: center;
font-size: 18px;
font-weight: bold;
color: #050505;
cursor: pointer;
transition: background-color 0.3s ease;
}
.lookbook__btn{
    background-color: #000000;
    border: 1px solid #ffffff;
}
.lookbook__btn_white {
    color: #ffffff;
}
.lookbook__btn_red {
    color: #b84b27;
}
</style>
</head>
<body>

<div class="container">
<a href="https://t.me/sveta_kosovska" class="btn btn-telegram">Telegram</a>
<a href="https://www.instagram.com/sveta_kosovska" class="btn btn-instagram">Instagram</a>       
<a href="https://t.me/+i8D-g8m5_Ak2MDNi" class="btn lookbook__btn lookbook__btn_white">LookBook</a>
<a href="https://ssk24test.my.canva.site/daglhozlvg0" class="btn btn-other">Ціни на послуги</a>
<a href="https://t.me/kosovskamanager" class="btn btn-support">Підтримка</a>
</div>

</body>
</html>

    """
    return render_template_string(html_template)


@app.route('/payment_callback', methods=['POST'])
def callback():
    data_str = request.form.to_dict()

    if not data_str:
        return jsonify({"error": "No data received"}), 400

    try:
        data_json_str = list(data_str.keys())[0]
        data = json.loads(data_json_str)
    except (IndexError, json.JSONDecodeError):
        return jsonify({"error": "Invalid JSON data"}), 400

    # Основные данные
    order_reference = data.get('orderReference')
    if not order_reference:
        return jsonify({"error": "Missing order reference"}), 400

    processing_time = int(time.time())
    status = 'accept'
    user_id = extract_user_id_from_reference(order_reference)
    signature = generate_signature(order_reference, status, processing_time)

    def generate_response():
        return {
            "orderReference": order_reference,
            "status": status,
            "time": processing_time,
            "signature": signature
        }

    # Обработка статусов
    transaction_status = data.get("transactionStatus")
    payment_sys = data.get("paymentSystem")

    if transaction_status == "Approved":
        add_user_to_channel(user_id, payment_sys)

    elif transaction_status in {"Declined", "Expired", "Refunded"}:
        delete_user_from_channel(user_id)

    print(data)
    return jsonify(generate_response()), 200


@app.route('/pay/<int:user_id>')
def pay(user_id):
    amount = 599
    currency = "UAH"
    product_name = ["Subscription to Telegram Channel"]
    product_price = [599]
    product_count = [1]
    order_date = int(time.time())
    today = datetime.now()
    future_date = today + timedelta(days=30)
    date_next = future_date.strftime("%d.%m.20%y")
    order_reference = f"invoice_{user_id}_{order_date}"

    # Генеруємо підпис
    signature = generate_merchant_signature(
        MERCHANT_ACCOUNT,
        MERCHANT_DOMAIN,
        order_reference,
        order_date,
        amount,
        currency,
        product_name,
        product_price,
        product_count
    )

    html_content = f"""
    <html>
      <body>
        <form id="wayforpay_form" action="https://secure.wayforpay.com/pay" method="POST">
            <input type="hidden" name="merchantAccount" value="{MERCHANT_ACCOUNT}">
            <input type="hidden" name="merchantDomainName" value="{MERCHANT_DOMAIN}">
            <input type="hidden" name="serviceUrl" value="{MERCHANT_DOMAIN}/payment_callback">
            <input type="hidden" name="orderReference" value="{order_reference}">
            <input type="hidden" name="orderDate" value="{order_date}">
            <input type="hidden" name="amount" value="{amount}">
            <input type="hidden" name="currency" value="UAH">
            <input type="hidden" name="productName[]" value="{product_name[0]}">
            <input type="hidden" name="productPrice[]" value="{amount}">
            <input type="hidden" name="productCount[]" value="1">
            <input type="hidden" name="regularOn" value="1">
            <input type="hidden" name="regularBehavior" value="preset">
            <input type="hidden" name="regularAmount" value="{amount}">
            <input type="hidden" name="regularMode" value="monthly">
            <input type="hidden" name="regularCount" value="24">
            <input type="hidden" name="dateNext" value="{date_next}">
            <input type="hidden" name="merchantSignature" value="{signature}">
            <input type="submit" value="Оплатити">
        </form>

        <script type="text/javascript">
            document.getElementById('wayforpay_form').submit();
        </script>
      </body>
    </html>
    """
    return render_template_string(html_content)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
