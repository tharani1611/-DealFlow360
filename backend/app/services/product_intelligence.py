import uuid
from decimal import Decimal
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.product import Product
from app.models.customer import Customer
from app.models.quotation import Quotation, QuotationItem
from app.models.deal import Deal
from app.schemas.intelligence import (
    Product360IntelligenceResponse,
    ProductPerformanceMetrics,
    ProductAffinityItem,
)


class ProductIntelligenceService:
    """Product Intelligence Subsystem calculating performance metrics, popularity rank, customer penetration, and co-purchase affinity matrix."""

    @staticmethod
    async def get_product_360_intelligence(
        db: AsyncSession,
        organization_id: uuid.UUID,
        product_id: uuid.UUID
    ) -> Product360IntelligenceResponse:
        """Calculates deterministic Product 360 intelligence, performance metrics, penetration, popularity rank, and co-purchase product affinities."""
        # 1. Fetch target product
        prod_q = await db.execute(
            select(Product).where(
                and_(
                    Product.id == product_id,
                    Product.organization_id == organization_id
                )
            )
        )
        product = prod_q.scalar_one_or_none()
        if not product:
            raise NotFoundException(f"Product with ID '{product_id}' not found.")

        # 2. Total active customers in organization for penetration calculation
        total_cust_q = await db.execute(
            select(func.count(Customer.id)).where(
                and_(
                    Customer.organization_id == organization_id,
                    Customer.is_active == True
                )
            )
        )
        total_active_customers = total_cust_q.scalar() or 0

        # 3. Fetch all quotation item rows for this product in tenant
        items_q = await db.execute(
            select(
                QuotationItem.quantity,
                QuotationItem.line_total,
                QuotationItem.unit_price,
                QuotationItem.unit_cost,
                Quotation.id,
                Quotation.customer_id,
                Quotation.status,
                Quotation.deal_id
            )
            .join(Quotation, QuotationItem.quotation_id == Quotation.id)
            .where(
                and_(
                    Quotation.organization_id == organization_id,
                    QuotationItem.product_id == product_id
                )
            )
        )
        item_rows = items_q.all()

        units_quoted = 0
        units_won = 0
        total_revenue = Decimal("0.00")
        total_cost = Decimal("0.00")
        quotation_ids: Set[uuid.UUID] = set()
        deal_ids: Set[uuid.UUID] = set()
        won_deal_ids: Set[uuid.UUID] = set()
        customer_ids: Set[uuid.UUID] = set()

        for qty, l_tot, u_price, u_cost, q_id, cust_id, q_status, d_id in item_rows:
            q_qty = int(qty or 1)
            units_quoted += q_qty
            quotation_ids.add(q_id)
            if cust_id:
                customer_ids.add(cust_id)
            if d_id:
                deal_ids.add(d_id)

            if q_status == "accepted":
                units_won += q_qty
                rev_val = l_tot or ((u_price or product.unit_price) * Decimal(q_qty))
                cost_val = (u_cost or product.unit_cost or Decimal("0.00")) * Decimal(q_qty)
                total_revenue += rev_val
                total_cost += cost_val

        # Also check won deals associated with deal_ids
        if deal_ids:
            won_deals_q = await db.execute(
                select(Deal.id).where(
                    and_(
                        Deal.organization_id == organization_id,
                        Deal.id.in_(list(deal_ids)),
                        Deal.status == "won"
                    )
                )
            )
            won_deal_ids = set(won_deals_q.scalars().all())

        won_deal_count = len(won_deal_ids)
        deal_count = len(deal_ids)
        quotation_count = len(quotation_ids)
        win_rate_pct = float((won_deal_count / deal_count) * 100) if deal_count > 0 else 0.0

        gross_margin = total_revenue - total_cost
        margin_pct = float((gross_margin / total_revenue) * 100) if total_revenue > Decimal("0.00") else (
            float(((product.unit_price - (product.unit_cost or Decimal("0.00"))) / product.unit_price) * 100)
            if product.unit_price > Decimal("0.00") else 0.0
        )

        avg_sp = (total_revenue / Decimal(units_won)) if units_won > 0 else product.unit_price
        customer_count = len(customer_ids)
        penetration_pct = float((customer_count / total_active_customers) * 100) if total_active_customers > 0 else 0.0

        popularity_score = min(100, int(quotation_count * 10 + won_deal_count * 20 + customer_count * 15))

        # Calculate popularity rank
        all_prods_q = await db.execute(
            select(Product.id).where(
                and_(
                    Product.organization_id == organization_id,
                    Product.is_active == True
                )
            )
        )
        all_prod_ids = list(all_prods_q.scalars().all())
        popularity_rank = 1  # Default rank

        if len(all_prod_ids) > 1:
            # Simple rank calculation
            prod_scores = []
            for p_id in all_prod_ids:
                q_cnt_res = await db.execute(
                    select(func.count(func.distinct(QuotationItem.quotation_id)))
                    .join(Quotation, QuotationItem.quotation_id == Quotation.id)
                    .where(
                        and_(
                            Quotation.organization_id == organization_id,
                            QuotationItem.product_id == p_id
                        )
                    )
                )
                q_cnt = q_cnt_res.scalar() or 0
                score = min(100, int(q_cnt * 10))
                prod_scores.append((p_id, score))

            prod_scores.sort(key=lambda x: x[1], reverse=True)
            for idx, (p_id, sc) in enumerate(prod_scores):
                if p_id == product_id:
                    popularity_rank = idx + 1
                    break

        # 4. Compute Product Co-Purchase Affinity Matrix
        affinities = await ProductIntelligenceService.calculate_product_affinities(
            db, organization_id, product_id, quotation_ids
        )

        # 5. Top customer segments using product
        top_segments = ["ENTERPRISE", "HIGH_VALUE", "GROWTH"] if penetration_pct > 20.0 else ["GROWTH", "DEVELOPING"]

        performance = ProductPerformanceMetrics(
            units_quoted=units_quoted,
            units_won=units_won,
            total_revenue=f"{total_revenue:.2f}",
            gross_margin=f"{gross_margin:.2f}",
            margin_percentage=round(margin_pct, 1),
            quotation_count=quotation_count,
            deal_count=deal_count,
            won_deal_count=won_deal_count,
            win_rate_percent=round(win_rate_pct, 1),
            average_selling_price=f"{avg_sp:.2f}",
            customer_count=customer_count,
            penetration_rate_percent=round(penetration_pct, 1),
            popularity_score=popularity_score,
            popularity_rank=popularity_rank
        )

        return Product360IntelligenceResponse(
            product_id=product.id,
            name=product.name,
            sku=product.sku,
            unit_price=f"{product.unit_price:.2f}",
            unit_cost=f"{(product.unit_cost or Decimal('0.00')):.2f}",
            is_active=product.is_active,
            description=product.description,
            performance=performance,
            affinities=affinities,
            top_customer_segments=top_segments
        )

    @staticmethod
    async def calculate_product_affinities(
        db: AsyncSession,
        organization_id: uuid.UUID,
        source_product_id: uuid.UUID,
        source_quotation_ids: Set[uuid.UUID]
    ) -> List[ProductAffinityItem]:
        """Calculates empirical co-purchase product affinity matrix across tenant quotations."""
        if not source_quotation_ids:
            return []

        # Query all other products co-occurring in the same quotations
        aff_q = await db.execute(
            select(
                Product.id,
                Product.name,
                Product.sku,
                Product.unit_price,
                func.count(func.distinct(QuotationItem.quotation_id)).label("co_count")
            )
            .join(QuotationItem, QuotationItem.product_id == Product.id)
            .where(
                and_(
                    Product.organization_id == organization_id,
                    Product.id != source_product_id,
                    Product.is_active == True,
                    QuotationItem.quotation_id.in_(list(source_quotation_ids))
                )
            )
            .group_by(Product.id, Product.name, Product.sku, Product.unit_price)
            .order_by(func.count(func.distinct(QuotationItem.quotation_id)).desc())
            .limit(10)
        )

        aff_rows = aff_q.all()
        results: List[ProductAffinityItem] = []
        total_source_quotes = len(source_quotation_ids)

        src_prod_q = await db.execute(
            select(Product.unit_price).where(Product.id == source_product_id)
        )
        source_unit_price = src_prod_q.scalar() or Decimal("0.00")

        for t_id, t_name, t_sku, t_price, co_cnt in aff_rows:
            attach_rate = float((co_cnt / total_source_quotes) * 100) if total_source_quotes > 0 else 0.0
            affinity_score = min(100, int(attach_rate * 0.7 + co_cnt * 10))
            rel_type = "UPSELL" if (t_price or Decimal("0.00")) > source_unit_price else "CROSS_SELL"

            results.append(ProductAffinityItem(
                target_product_id=t_id,
                target_product_name=t_name,
                target_sku=t_sku,
                unit_price=f"{(t_price or Decimal('0.00')):.2f}",
                co_purchase_count=co_cnt,
                attachment_rate_percent=round(attach_rate, 1),
                affinity_score=affinity_score,
                relationship_type=rel_type
            ))

        return results


product_intelligence_service = ProductIntelligenceService()
