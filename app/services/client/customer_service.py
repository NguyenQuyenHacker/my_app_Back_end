from app.models.customer_model import Customer


def build_customer_overview(customer: Customer) -> dict:
    return {
        "phone": customer.phone,
        "full_name": customer.full_name,
        "email": customer.email,
        "permanent_address": customer.permanent_address,
        "current_address": customer.current_address,
        "dob": customer.date_of_birth,
        "gender": customer.gender,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
    }