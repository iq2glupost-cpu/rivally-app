import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RAINFOREST_API_KEY")


def analyze_buybox(asin, target_seller_id):
    url = "https://api.rainforestapi.com/request"

    params = {
        "api_key": API_KEY,
        "type": "product",
        "amazon_domain": "amazon.com",
        "asin": asin,
        "zip_code": "10001"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        product = data.get("product", {})
        buybox = product.get("buybox_winner", {})
        fulfillment = buybox.get("fulfillment", {})

        # =========================
        # PRICE
        # =========================
        price = (buybox.get("price") or {}).get("value", 0.0)

        # =========================
        # SELLER DETECTION
        # =========================
        winner_id = ""
        winner_name = "Unknown Seller"

        if buybox.get("seller"):
            winner_id = buybox["seller"].get("id", "")
            winner_name = buybox["seller"].get("name", "Unknown Seller")

        elif buybox.get("merchant_info"):
            winner_id = buybox["merchant_info"].get("id", "")
            winner_name = buybox["merchant_info"].get("name", "Unknown Seller")

        elif fulfillment.get("third_party_seller"):
            seller = fulfillment["third_party_seller"]
            winner_id = seller.get("id", "")
            winner_name = seller.get("name", "Unknown Seller")

            if not winner_id and seller.get("link"):
                link = seller["link"]
                if "seller=" in link:
                    winner_id = link.split("seller=")[1].split("&")[0]

        is_amazon = buybox.get("is_amazon", fulfillment.get("is_sold_by_amazon", False))
        is_fba = buybox.get("is_fba", fulfillment.get("is_fulfilled_by_amazon", False))

        if is_amazon:
            winner_name = "Amazon.com"

        # =========================
        # SELLER COUNT
        # =========================
        total_sellers = 1

        if buybox.get("mixed_offers_count") is not None:
            total_sellers = int(buybox.get("mixed_offers_count"))

        elif product.get("mixed_offers_count") is not None:
            total_sellers = int(product.get("mixed_offers_count"))

        elif product.get("offers_count") is not None:
            total_sellers = int(product.get("offers_count"))

        elif product.get("offers"):
            total_sellers = len(product.get("offers"))

        if total_sellers < 1:
            total_sellers = 1

        # =========================
        # 🔥 BASIC MODE (NO SELLER ID)
        # =========================
        if not target_seller_id:
            headline = f"{total_sellers} sellers detected on this listing"

            details = (
                f"There are {total_sellers} active sellers competing for the Buy Box.\n\n"
                f"Current Buy Box price: ${price}\n\n"
                "Enter your Seller ID to see if you're winning or losing the Buy Box.\n\n"
                "This is only a surface-level analysis."
            )

            return {
                "status": "success",
                "data": {
                    "asin": asin,
                    "market": {
                        "total_sellers": total_sellers
                    },
                    "diagnosis": {
                        "headline": headline,
                        "details": details,
                        "risk_block": "Limited analysis",
                        "hidden_trigger": "Unlock full Buy Box intelligence with Seller ID",
                        "threat_level": "MEDIUM" if total_sellers > 1 else "LOW"
                    }
                }
            }

        # =========================
        # FULL MODE (WITH SELLER ID)
        # =========================
        target_id = target_seller_id.strip()
        holds = (target_id == winner_id.strip())

        if not holds:
            if target_id in json.dumps(buybox):
                holds = True

        if holds:
            if total_sellers == 1:
                risk_level = "HIGH"
                risk_score = 70
            elif total_sellers <= 3:
                risk_level = "MEDIUM"
                risk_score = 55
            else:
                risk_level = "HIGH"
                risk_score = 75
        else:
            risk_level = "CRITICAL"
            risk_score = 92

        if holds:
            headline = "You Control the Buy Box — But You Are Exposed"
            details = (
                f"You currently hold the Buy Box at ${price}.\n\n"
                f"There are at least {total_sellers} active sellers.\n\n"
                "Buy Box ownership can shift quickly."
            )
        else:
            headline = "You Are Losing the Buy Box"
            details = (
                f"Current Buy Box price: ${price}\n\n"
                "A competitor is dominating the listing.\n\n"
                "Multiple signals are affecting your position."
            )

        return {
            "status": "success",
            "data": {
                "asin": asin,
                "buybox": {
                    "holds": holds,
                    "price": price,
                    "is_fba": is_fba
                },
                "market": {
                    "total_sellers": total_sellers
                },
                "risk": {
                    "score": risk_score,
                    "level": risk_level
                },
                "diagnosis": {
                    "headline": headline,
                    "details": details,
                    "risk_block": f"Risk level: {risk_level}",
                    "hidden_trigger": "Full competitive signals hidden",
                    "threat_level": risk_level
                }
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
