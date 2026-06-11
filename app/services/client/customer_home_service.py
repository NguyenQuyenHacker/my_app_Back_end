from app.models.customer_model import Customer


def build_customer_home(customer: Customer) -> dict:
    return {
        "greeting_name": customer.full_name,
        "cards": {
            "accounts": {
                "title": "Tài khoản",
                "icon": "account_balance_wallet",
                "to": "/customer/accounts",
            },
            "transactions": {
                "title": "Giao dịch",
                "icon": "history",
                "to": "/customer/transfer",
            },
            "loans": {
                "title": "Hồ sơ vay",
                "icon": "description",
                "to": "/customer/loans",
                "desc": "1 Khoản vay mua nhà",
                "status": "Đang thẩm định",
            },
            "cards": {
                "title": "Thẻ tín dụng",
                "icon": "credit_card",
                "to": "/customer/cards",
                "desc": "Visa Signature",
                "limit": "45tr",
            },
        },
    }
