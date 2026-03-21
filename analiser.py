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
        # SELLER DETECTION (ROBUST)
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

            # fallback iz URL-a
            if not winner_id and seller.get("link"):
                link = seller["link"]
                if "seller=" in link:
                    winner_id = link.split("seller=")[1].split("&")[0]

        is_amazon = buybox.get("is_amazon", fulfillment.get("is_sold_by_amazon", False))
        is_fba = buybox.get("is_fba", fulfillment.get("is_fulfilled_by_amazon", False))

        if is_amazon:
            winner_name = "Amazon.com"

        # =========================
        # SELLER COUNT (FINAL FIX)
        # =========================

        total_sellers = 1

        # 🔥 NAJBITNIJE - iz buybox_winner
        if buybox.get("mixed_offers_count") is not None:
            total_sellers = int(buybox.get("mixed_offers_count"))

        # fallback (retko)
        elif product.get("mixed_offers_count") is not None:
            total_sellers = int(product.get("mixed_offers_count"))

        elif product.get("offers_count") is not None:
            total_sellers = int(product.get("offers_count"))

        elif product.get("offers"):
            total_sellers = len(product.get("offers"))

        # sigurnost
        if total_sellers < 1:
            total_sellers = 1



        # =========================
        # BUY BOX LOGIC
        # =========================
        target_id = target_seller_id.strip()
        holds = (target_id == winner_id.strip())

        # fallback (Rainforest edge case)
        if not holds:
            if target_id in json.dumps(buybox):
                holds = True

        # =========================
        # RISK ENGINE
        # =========================
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

        # =========================
        # COPY (APPLE STYLE)
        # =========================
        if holds:
            headline = "You Control the Buy Box — But You Are Exposed"

            details = (
                f"You currently hold the Buy Box at ${price}.\n\n"
                f"There are at least {total_sellers} active sellers on this listing.\n\n"
                "This may not reflect the full scope of competitive pressure.\n"
                "Buy Box ownership in environments like this can shift quickly.\n\n"
                "A single pricing or fulfillment change can remove you instantly."
            )
        else:
            headline = "You Are Losing the Buy Box"

            details = (
                "A competing seller is currently dominating the Buy Box.\n\n"
                f"Current Buy Box price: ${price}\n\n"
                "Price and fulfillment advantage detected.\n\n"
                "This may not reflect the full scope of factors affecting your position.\n"
                "Additional competitive signals are influencing Buy Box rotation."
            )

        # =========================
        # PREMIUM RISK BLOCK
        # =========================
        risk_block = (
            f"Risk level: {risk_level}\n\n"
            "Listings in this state typically experience increased volatility.\n\n"
            "Performance can decline once competitive pressure intensifies.\n\n"
            "These conditions tend to escalate rather than stabilize."
        )

        # =========================
        # HIDDEN HOOK
        # =========================
        hidden = (
            "This view reflects only surface-level signals.\n"
            "Additional factors affecting Buy Box allocation are not visible here.\n\n"
            "Continuous monitoring is required to fully understand these changes."
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
                    "risk_block": risk_block,
                    "hidden_trigger": hidden
                }
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
