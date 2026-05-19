from app.models.customer_model import Customer


def build_customer_info(customer: Customer) -> dict:
    return {
        "phone": customer.phone,
        "full_name": customer.full_name,
        "email": customer.email,
        "permanent_address": customer.permanent_address,
        "current_address": customer.current_address,
        "dob": customer.date_of_birth,
        "gender": customer.gender,
        "cccd_number": customer.cccd_number,
        "identity_issue_date": customer.identity_issue_date,
        "identity_expiry_date": customer.identity_expiry_date,
        "identity_issue_place": customer.identity_issue_place,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
    }
