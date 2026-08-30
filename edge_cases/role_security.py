"""
edge_cases/role_security.py
Scenario 4 (§4.4): Role-Based Security & Multi-Tenant Entitlements Scenario

Enforces multi-tenant isolation, role entitlements, parameterized SQL query rewriting,
dynamic cryptographic PII / margin masking, and GoRules Rules 13-16 role authorization.

Implements:
  1. SecurityContext Pydantic Model (user_id, tenant_id, roles, permitted_metrics,
     permitted_dimensions, permitted_regions, can_view_margins, can_view_pii, max_approval_limit).
  2. Multi-tenant AST / Parameterized SQL Query Rewriter:
     - Injects WHERE tenant_id = :tenant_id AND region IN (:permitted_regions)
     - Maps logical table names to physical canonical measurement tables
     - Injects safety LIMIT 1000
  3. Pre-Synthesis ABAC Metric & Dimension Filtering:
     - Prunes unwhitelisted metrics and unauthorized dimension slices
  4. Dynamic Cryptographic PII & Financial Margin Masking:
     - Customer Email -> CUST-***-SHA256:7f8a... (SHA-256 hash)
     - Customer Phone -> [REDACTED - PII]
     - Gross Margin % -> [REDACTED - CONFIDENTIAL]
     - Unit COGS ($)  -> [REDACTED - FINANCIAL]
  5. GoRules Rules 13-16 Role Authorization Enforcement:
     - Rule 13 (ENGINEERING): Infrastructure only, financial discounts PROHIBITED
     - Rule 14 (SALES): Sales quotes only, infrastructure restarts PROHIBITED
     - Rule 15 (EXECUTIVE): Strategic pricing & budget levers AUTHORIZED up to limit
     - Rule 16 (SPEND_LIMIT): ActionCost > max_approval_limit -> Downgraded to HUMAN_REVIEW (CFO sign-off)
  6. Runtime [MOCK DATA] notification.
"""

from __future__ import annotations

import hashlib
import re
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import sqlparse
from pydantic import BaseModel, Field


MOCK_NOTICE = "[MOCK DATA] This output uses synthetic/simulated data. Replace with real ingested data."


class PersonaRole(str, Enum):
    EXECUTIVE = "EXECUTIVE"
    FINANCE = "FINANCE"
    ENGINEERING = "ENGINEERING"
    SALES = "SALES"


class SecurityContext(BaseModel):
    """
    SecurityContext model (§4.4) defining authenticated tenant and role entitlements.
    """
    user_id: str = Field(..., description="Unique authenticated user identity")
    tenant_id: str = Field(..., description="Multi-tenant organization boundary")
    roles: List[PersonaRole] = Field(..., description="Active user roles")
    permitted_metrics: List[str] = Field(default_factory=list, description="Whitelisted KPI IDs")
    permitted_dimensions: List[str] = Field(default_factory=list, description="Whitelisted dimensions")
    permitted_regions: List[str] = Field(default_factory=list, description="Whitelisted geographic regions")
    can_view_margins: bool = Field(default=False, description="Entitlement for gross margin/COGS")
    can_view_pii: bool = Field(default=False, description="Entitlement for customer PII")
    max_approval_limit: float = Field(default=0.0, description="Financial authority threshold ($USD)")


class RewrittenQuery(BaseModel):
    original_sql: str
    rewritten_sql: str
    bound_parameters: Dict[str, Any]
    tenant_isolated: bool
    region_isolated: bool


class SQLRewriter:
    """
    AST & parameterized SQL rewriter that intercepts domain agent queries
    and enforces multi-tenant boundary isolation and regional filtering.
    """

    TABLE_MAPPINGS = {
        "customer_metrics": "customer_measurements",
        "kpi_metrics": "canonical_measurements",
        "orders_table": "orders_measurements",
        "marketing_data": "marketing_measurements"
    }

    @classmethod
    def rewrite_query(
        cls,
        sql: str,
        security_ctx: SecurityContext,
        target_kpi: Optional[str] = None
    ) -> RewrittenQuery:
        """
        Rewrites incoming agent SQL query to inject tenant_id and region scoping.
        """
        cleaned_sql = sql.strip().rstrip(";")
        
        # 1. Map logical table names to canonical tables
        rewritten = cleaned_sql
        for logical_tbl, physical_tbl in cls.TABLE_MAPPINGS.items():
            pattern = re.compile(rf"\b{logical_tbl}\b", re.IGNORECASE)
            rewritten = pattern.sub(physical_tbl, rewritten)

        # 2. Extract WHERE clause or inject WHERE
        has_where = bool(re.search(r"\bWHERE\b", rewritten, re.IGNORECASE))
        
        tenant_predicate = "tenant_id = :tenant_id"
        region_predicate = "region IN (:permitted_regions)" if security_ctx.permitted_regions else None

        injected_predicates = [tenant_predicate]
        if region_predicate:
            injected_predicates.append(region_predicate)

        combined_predicates = " AND ".join(injected_predicates)

        if has_where:
            # Inject after WHERE
            where_match = re.search(r"\bWHERE\b", rewritten, re.IGNORECASE)
            if where_match:
                idx = where_match.end()
                rewritten = rewritten[:idx] + f" ({combined_predicates}) AND" + rewritten[idx:]
        else:
            # Check for GROUP BY, ORDER BY, LIMIT
            split_match = re.search(r"\b(GROUP\s+BY|ORDER\s+BY|LIMIT)\b", rewritten, re.IGNORECASE)
            if split_match:
                idx = split_match.start()
                rewritten = rewritten[:idx] + f" WHERE {combined_predicates} " + rewritten[idx:]
            else:
                rewritten = f"{rewritten} WHERE {combined_predicates}"

        # 3. Ensure LIMIT safety clause
        if not re.search(r"\bLIMIT\b", rewritten, re.IGNORECASE):
            rewritten = f"{rewritten} LIMIT 1000"

        # Parameter binding
        bound_params: Dict[str, Any] = {
            "tenant_id": security_ctx.tenant_id
        }
        if security_ctx.permitted_regions:
            bound_params["permitted_regions"] = security_ctx.permitted_regions
        if target_kpi:
            bound_params["kpi_id"] = target_kpi

        # Format with sqlparse
        formatted_sql = sqlparse.format(rewritten, reindent=True, keyword_case="upper")

        return RewrittenQuery(
            original_sql=sql,
            rewritten_sql=formatted_sql,
            bound_parameters=bound_params,
            tenant_isolated=True,
            region_isolated=bool(security_ctx.permitted_regions)
        )


class DataMasker:
    """
    Cryptographic and redaction masking engine for PII and financial metrics.
    """

    EMAIL_REGEX = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
    PHONE_REGEX = re.compile(r"(\+?[0-9]{1,3}[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})")

    @classmethod
    def mask_email(cls, email: str, secret_salt: str = "enterprise_bi_salt_2026") -> str:
        """Masks email using SHA-256 truncated hash: CUST-***-SHA256:7f8a..."""
        h = hashlib.sha256(f"{email}{secret_salt}".encode("utf-8")).hexdigest()[:8]
        return f"CUST-***-SHA256:{h}"

    @classmethod
    def mask_record(cls, record: Dict[str, Any], security_ctx: SecurityContext) -> Dict[str, Any]:
        """
        Applies dynamic field-level masking based on SecurityContext entitlements.
        """
        masked = dict(record)

        # 1. PII Masking
        if not security_ctx.can_view_pii:
            if "customer_email" in masked:
                masked["customer_email"] = cls.mask_email(str(masked["customer_email"]))
            if "customer_phone" in masked:
                masked["customer_phone"] = "[REDACTED - PII]"
            if "contact_name" in masked:
                masked["contact_name"] = "CUST-***"

        # 2. Financial Margins & Unit COGS Masking
        if not security_ctx.can_view_margins:
            if "gross_margin_pct" in masked:
                masked["gross_margin_pct"] = "[REDACTED - CONFIDENTIAL]"
            if "gross_margin" in masked:
                masked["gross_margin"] = "[REDACTED - CONFIDENTIAL]"
            if "unit_cogs" in masked:
                masked["unit_cogs"] = "[REDACTED - FINANCIAL]"
            if "cost_of_goods_sold" in masked:
                masked["cost_of_goods_sold"] = "[REDACTED - FINANCIAL]"

        return masked

    @classmethod
    def mask_text_narrative(cls, text: str, security_ctx: SecurityContext) -> str:
        """
        Applies regex-based dynamic redaction to generated persona narrative stories.
        """
        output = text

        if not security_ctx.can_view_pii:
            # Mask emails
            output = cls.EMAIL_REGEX.sub(lambda m: cls.mask_email(m.group(0)), output)
            # Mask phone numbers
            output = cls.PHONE_REGEX.sub("[REDACTED - PII]", output)

        if not security_ctx.can_view_margins:
            # Mask margin percentages like 74.2% margin or COGS $142.50
            output = re.sub(r"(\b\d+(\.\d+)?%\s*(gross\s*)?margin\b)", "[REDACTED - CONFIDENTIAL]", output, flags=re.IGNORECASE)
            output = re.sub(r"(\bCOGS\s*(of\s*)?\$?\d+(\.\d+)?\b)", "[REDACTED - FINANCIAL]", output, flags=re.IGNORECASE)

        return output


class ABACFilter:
    """
    Attribute-Based Access Control filter that prunes unauthorized metrics
    and dimension slices from findings prior to synthesis.
    """

    @classmethod
    def filter_findings(
        cls,
        findings: List[Dict[str, Any]],
        security_ctx: SecurityContext
    ) -> List[Dict[str, Any]]:
        """
        Prunes findings associated with non-permitted metrics or unauthorized dimensions.
        """
        permitted_metrics_set = set(m.lower() for m in security_ctx.permitted_metrics)
        permitted_dims_set = set(d.lower() for d in security_ctx.permitted_dimensions)

        sanitized_findings: List[Dict[str, Any]] = []

        for f in findings:
            metric_name = str(f.get("metric", "")).lower()
            # If permitted_metrics is defined, check membership
            if permitted_metrics_set and metric_name and metric_name not in permitted_metrics_set:
                continue  # Prune unauthorized metric

            # Clean dimensions
            clean_f = dict(f)
            if "dimensions" in clean_f and isinstance(clean_f["dimensions"], dict):
                filtered_dims = {}
                for dim_key, dim_val in clean_f["dimensions"].items():
                    if not permitted_dims_set or dim_key.lower() in permitted_dims_set:
                        filtered_dims[dim_key] = dim_val
                    else:
                        filtered_dims[dim_key] = "[UNAUTHORIZED_DIMENSION]"
                clean_f["dimensions"] = filtered_dims

            sanitized_findings.append(clean_f)

        return sanitized_findings


class GovernanceRoleAuthorizer:
    """
    Enforces GoRules Rules 13-16 role authorization checks (§4.4, §4.2):
      - Rule 13: PersonaRole == ENGINEERING -> Restricts to infrastructure/code rollbacks; discount PROHIBITED.
      - Rule 14: PersonaRole == SALES -> Restricts to pricing quotes; infra restarts PROHIBITED.
      - Rule 15: PersonaRole == EXECUTIVE -> Strategic pricing & budget levers AUTHORIZED up to max_approval_limit.
      - Rule 16: ActionCost > SecurityContext.max_approval_limit -> Downgraded to HUMAN_REVIEW with CFO sign-off.
    """

    @classmethod
    def authorize_action(
        cls,
        action_type: str,
        action_cost: float,
        security_ctx: SecurityContext
    ) -> Dict[str, Any]:
        primary_role = security_ctx.roles[0] if security_ctx.roles else PersonaRole.SALES
        action_lower = action_type.lower()

        # Rule 16: Spend limit check
        if action_cost > security_ctx.max_approval_limit:
            return {
                "rule_applied": 16,
                "decision_right": "HUMAN_REVIEW",
                "action_type": action_type,
                "action_cost": action_cost,
                "authorized": False,
                "reason": f"Rule 16: Action cost (${action_cost:,.2f}) exceeds role approval limit (${security_ctx.max_approval_limit:,.2f}). Requires CFO sign-off."
            }

        # Rule 13: ENGINEERING
        if primary_role == PersonaRole.ENGINEERING:
            if "discount" in action_lower or "pricing" in action_lower or "budget" in action_lower:
                return {
                    "rule_applied": 13,
                    "decision_right": "PROHIBITED",
                    "action_type": action_type,
                    "action_cost": action_cost,
                    "authorized": False,
                    "reason": "Rule 13: Engineering role is restricted to infrastructure/code rollbacks. Financial discount levers are PROHIBITED."
                }
            elif "rollback" in action_lower or "restart" in action_lower or "infrastructure" in action_lower:
                return {
                    "rule_applied": 13,
                    "decision_right": "AUTHORIZED",
                    "action_type": action_type,
                    "action_cost": action_cost,
                    "authorized": True,
                    "reason": "Rule 13: Engineering role is AUTHORIZED for infrastructure and code deployment rollbacks."
                }

        # Rule 14: SALES
        if primary_role == PersonaRole.SALES:
            if "rollback" in action_lower or "restart" in action_lower or "infrastructure" in action_lower:
                return {
                    "rule_applied": 14,
                    "decision_right": "PROHIBITED",
                    "action_type": action_type,
                    "action_cost": action_cost,
                    "authorized": False,
                    "reason": "Rule 14: Sales role is restricted to pricing quotes and customer outreach. Infrastructure rollbacks are PROHIBITED."
                }
            elif "discount" in action_lower or "quote" in action_lower or "outreach" in action_lower:
                return {
                    "rule_applied": 14,
                    "decision_right": "AUTHORIZED",
                    "action_type": action_type,
                    "action_cost": action_cost,
                    "authorized": True,
                    "reason": f"Rule 14: Sales role is AUTHORIZED for customer discount levers within limit (${security_ctx.max_approval_limit:,.2f})."
                }

        # Rule 15: EXECUTIVE / FINANCE
        if primary_role in [PersonaRole.EXECUTIVE, PersonaRole.FINANCE]:
            return {
                "rule_applied": 15,
                "decision_right": "AUTHORIZED",
                "action_type": action_type,
                "action_cost": action_cost,
                "authorized": True,
                "reason": f"Rule 15: {primary_role.value} role is AUTHORIZED for strategic pricing and budget reallocation levers up to ${security_ctx.max_approval_limit:,.2f}."
            }

        return {
            "rule_applied": 20,
            "decision_right": "ALLOWED",
            "action_type": action_type,
            "action_cost": action_cost,
            "authorized": True,
            "reason": "Standard action within policy."
        }


class RoleSecurityScenarioRunner:
    """
    Demonstrates Scenario 4 (§4.4) across four enterprise personas:
      1. Executive Persona (Full access, high spend limit)
      2. Finance Persona (Margin access, moderate spend limit)
      3. Engineering Persona (Infra only, no PII, no margins)
      4. Sales Persona (Sales discounts only, regional scope, no margins)
    """

    def __init__(self):
        self.personas: Dict[str, SecurityContext] = {
            "executive": SecurityContext(
                user_id="usr_exec_001",
                tenant_id="tenant_acme_corp",
                roles=[PersonaRole.EXECUTIVE],
                permitted_metrics=["net_revenue", "gross_margin", "churn_rate", "cac", "ltv"],
                permitted_dimensions=["region", "sales_channel", "product_tier", "salary_band"],
                permitted_regions=["US-East", "US-West", "EU-Central", "APAC"],
                can_view_margins=True,
                can_view_pii=True,
                max_approval_limit=500000.0  # $500k limit
            ),
            "finance": SecurityContext(
                user_id="usr_fin_002",
                tenant_id="tenant_acme_corp",
                roles=[PersonaRole.FINANCE],
                permitted_metrics=["net_revenue", "gross_margin", "cogs", "refund_volume"],
                permitted_dimensions=["region", "sales_channel", "payment_processor"],
                permitted_regions=["US-East", "US-West", "EU-Central"],
                can_view_margins=True,
                can_view_pii=False,
                max_approval_limit=50000.0   # $50k limit
            ),
            "engineering": SecurityContext(
                user_id="usr_eng_003",
                tenant_id="tenant_acme_corp",
                roles=[PersonaRole.ENGINEERING],
                permitted_metrics=["checkout_error_rate", "latency_p99", "api_availability"],
                permitted_dimensions=["service_name", "host", "edge_pop"],
                permitted_regions=["US-East", "US-West"],
                can_view_margins=False,
                can_view_pii=False,
                max_approval_limit=5000.0    # $5k limit
            ),
            "sales": SecurityContext(
                user_id="usr_sales_004",
                tenant_id="tenant_acme_corp",
                roles=[PersonaRole.SALES],
                permitted_metrics=["net_revenue", "deal_pipeline", "conversion_rate"],
                permitted_dimensions=["sales_rep", "account_tier", "region"],
                permitted_regions=["US-East"],
                can_view_margins=False,
                can_view_pii=False,
                max_approval_limit=10000.0   # $10k limit
            )
        }

        self.sample_raw_record = {
            "customer_id": "cust_98741",
            "customer_name": "Alice Smith",
            "customer_email": "alice.smith@enterprise-client.com",
            "customer_phone": "+1 (415) 555-0199",
            "kpi_id": "net_revenue",
            "revenue_amount": 25000.0,
            "gross_margin_pct": "74.2%",
            "unit_cogs": "$142.50",
            "region": "US-East"
        }

        self.sample_narrative = (
            "Investigation Summary: Customer Alice Smith (contact: alice.smith@enterprise-client.com, "
            "+1 (415) 555-0199) was impacted by checkout downtime. The unit COGS of $142.50 resulted in a "
            "74.2% gross margin on the order. Recommended action: Grant 15% retention discount ($7,500 cost)."
        )

    def run_security_demonstration(self) -> Dict[str, Any]:
        """
        Executes end-to-end security demonstration for all 4 personas.
        """
        raw_agent_sql = "SELECT customer_id, customer_email, gross_margin, lifetime_value FROM customer_metrics WHERE kpi_id = 'net_revenue';"
        
        results: Dict[str, Any] = {}

        for role_name, ctx in self.personas.items():
            # 1. Multi-tenant SQL query rewriting
            rewritten = SQLRewriter.rewrite_query(raw_agent_sql, ctx, target_kpi="net_revenue")

            # 2. Dynamic Data Masking
            masked_record = DataMasker.mask_record(self.sample_raw_record, ctx)
            masked_story = DataMasker.mask_text_narrative(self.sample_narrative, ctx)

            # 3. GoRules Authorization Checks
            auth_discount = GovernanceRoleAuthorizer.authorize_action(
                action_type="Offer customer discount",
                action_cost=7500.0,
                security_ctx=ctx
            )
            auth_rollback = GovernanceRoleAuthorizer.authorize_action(
                action_type="Rollback deployment",
                action_cost=1000.0,
                security_ctx=ctx
            )
            auth_high_spend = GovernanceRoleAuthorizer.authorize_action(
                action_type="Paid advertising surge campaign",
                action_cost=75000.0,
                security_ctx=ctx
            )

            results[role_name] = {
                "security_context": ctx.model_dump(),
                "sql_rewritten": rewritten.model_dump(),
                "masked_record": masked_record,
                "masked_story": masked_story,
                "governance_decisions": {
                    "discount_7500": auth_discount,
                    "rollback_1000": auth_rollback,
                    "high_spend_75000": auth_high_spend
                }
            }

        return results


def run_scenario() -> Dict[str, Any]:
    """Entrypoint for Scenario 4."""
    print(MOCK_NOTICE)
    print("=" * 80)
    print("SCENARIO 4: ROLE-BASED SECURITY & MULTI-TENANT ENTITLEMENTS (§4.4)")
    print("=" * 80)

    runner = RoleSecurityScenarioRunner()
    results = runner.run_security_demonstration()

    print("\n1. MULTI-TENANT PARAMETERIZED SQL QUERY REWRITING (Engineering Persona vs Executive Persona):")
    print("-" * 80)
    eng_sql = results["engineering"]["sql_rewritten"]
    print("Original Agent Query:")
    print(f"  {eng_sql['original_sql']}")
    print("\nRewritten & Parameterized Multi-Tenant Query (Engineering Scope):")
    print(f"  {eng_sql['rewritten_sql']}")
    print(f"Bound Parameters: {eng_sql['bound_parameters']}")

    print("\n" + "-" * 80)
    print("2. DYNAMIC CRYPTOGRAPHIC DATA MASKING & MARGIN REDACTION BY PERSONA:")
    print(f"{'Field':<20} | {'Executive (Privileged)':<28} | {'Finance':<26} | {'Engineering / Sales':<26}")
    print("-" * 106)
    fields_to_show = ["customer_email", "customer_phone", "gross_margin_pct", "unit_cogs"]
    for f in fields_to_show:
        exec_val = str(results["executive"]["masked_record"].get(f, ""))
        fin_val = str(results["finance"]["masked_record"].get(f, ""))
        eng_val = str(results["engineering"]["masked_record"].get(f, ""))
        print(f"{f:<20} | {exec_val:<28} | {fin_val:<26} | {eng_val:<26}")
    print("-" * 106)

    print("\n3. DYNAMIC STORY NARRATIVE REDACTION:")
    print(f"[Engineering Persona Masked Narrative]:\n  {results['engineering']['masked_story']}")
    print(f"\n[Executive Persona Unmasked Narrative]:\n  {results['executive']['masked_story']}")

    print("\n" + "-" * 80)
    print("4. GORULES ROLE AUTHORIZATION DECISIONS (Rules 13-16):")
    for role_name in ["engineering", "sales", "finance", "executive"]:
        decisions = results[role_name]["governance_decisions"]
        print(f"\nPersona: {role_name.upper()}")
        for act_name, dec in decisions.items():
            print(f"  - Action '{dec['action_type']}' (${dec['action_cost']:,.2f}): Rule {dec['rule_applied']} -> {dec['decision_right']} ({dec['reason']})")
    print("=" * 80 + "\n")

    return results


if __name__ == "__main__":
    run_scenario()
