import json
import requests
import os

def handler(request):
    try:
        body = request.get_json()
        asin = body.get("asin")
        seller_id = body.get("seller_id")

        API_KEY = os.environ.get("RAINFOREST_API_KEY")

        url = "https://api.rainforestapi.com/request"
        params = {
            "api_key": API_KEY,
            "type": "product",
            "amazon_domain": "amazon.com",
            "asin": asin
        }

        response = requests.get(url, params=params)
        data = response.json()

        product = data.get("product", {})
        buybox = product.get("buybox_winner", {})

        # SELLER COUNT (ovo je ono što ti treba)
        sellers = buybox.get("mixed_offers_count", 1)

        price = buybox.get("price", {}).get("value", 0)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "data": {
                    "price": price,
                    "sellers": sellers
                }
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
