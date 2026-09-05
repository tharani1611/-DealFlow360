from fastapi import APIRouter, HTTPException, status
from app.api.v1 import (
    health, auth, customers, contacts, products, quotations, deals, activities, ai, intelligence, product_recommendation_rules, pricing, margins, discount_governance, discount_risk, approvals, copilot
)

api_router = APIRouter()

# Register core health endpoints
api_router.include_router(health.router, tags=["Health"])

# Register authentication router
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Register CRM Domain routers
api_router.include_router(customers.router, prefix="/customers", tags=["Customer Directory"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["Contact Directory"])
api_router.include_router(products.router, prefix="/products", tags=["Product Catalog"])
api_router.include_router(quotations.router, prefix="/quotations", tags=["Quotation Builder"])
api_router.include_router(deals.router, prefix="/deals", tags=["Sales Pipeline"])
api_router.include_router(activities.router, prefix="/activities", tags=["Activities & Workflow"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Intelligence"])
api_router.include_router(intelligence.router, prefix="/intelligence", tags=["CRM Intelligence"])
api_router.include_router(product_recommendation_rules.router, prefix="/product-recommendation-rules", tags=["Product Recommendation Rules"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["Pricing Engine"])
api_router.include_router(margins.router, prefix="/margins", tags=["Real-time Margin Engine"])
api_router.include_router(discount_governance.router, prefix="/discount-governance", tags=["Discount Governance"])
api_router.include_router(discount_risk.router, prefix="/discount-risk", tags=["Discount Risk Engine"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["Approval Engine"])
api_router.include_router(copilot.router, prefix="/copilot", tags=["AI Sales Copilot"])

# Module route prefixes specified in architecture
MODULE_PREFIXES = [
    ("users", "User Management"),
    ("portal", "Customer Negotiation Portal"),
    ("fulfillment", "Fulfillment Engine"),
    ("backorders", "Backorder Queue"),
    ("billing", "Hybrid Billing"),
    ("payments", "Payment Operations"),
    ("deal-health", "Deal Health Telemetry"),
    ("reports", "Reporting & Analytics"),
    ("admin", "System Administration")
]

# Register placeholder routers for all domain endpoints (returns 501 Not Implemented until domain phase)
for prefix, tag in MODULE_PREFIXES:
    module_router = APIRouter(prefix=f"/{prefix}", tags=[tag])

    @module_router.api_route("", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    @module_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def not_implemented_stub(prefix_name: str = prefix):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"The endpoint prefix '/api/v1/{prefix_name}' foundation is prepared. Domain logic will be implemented in its designated roadmap phase."
        )

    api_router.include_router(module_router)
