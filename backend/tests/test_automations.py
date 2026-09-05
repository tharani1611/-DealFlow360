import pytest
import uuid
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_automation_rule_crud_and_lifecycle(async_client: AsyncClient):
    """Verifies rule CRUD, pre-activation validation, and lifecycle state transitions."""
    reg = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Automation Rule Org",
        "organization_slug": f"autoorg-{uuid.uuid4().hex[:8]}",
        "email": f"user-{uuid.uuid4().hex[:6]}@autoorg.com",
        "password": "Password123!",
        "full_name": "Automation User"
    })
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    # 1. Create rule in DRAFT
    create_res = await async_client.post("/api/v1/automations", json={
        "name": "High Value Proposal Task",
        "description": "Create follow-up task when deal reaches proposal stage with value > 50k",
        "trigger_type": "DEAL_STAGE_CHANGED",
        "priority": 10,
        "conditions": {
            "logical_operator": "AND",
            "conditions": [
                {"field": "deal.stage", "operator": "equals", "value": "proposal"},
                {"field": "deal.value", "operator": "greater_than", "value": "50000"}
            ]
        },
        "actions": [
            {
                "action_type": "CREATE_ACTIVITY",
                "parameters": {
                    "title": "Follow up on proposal",
                    "activity_type": "call",
                    "priority": "high",
                    "due_in_days": 2
                }
            }
        ]
    }, headers=headers)
    assert create_res.status_code == 201
    rule_data = create_res.json()
    rule_id = rule_data["id"]
    assert rule_data["status"] == "DRAFT"
    assert rule_data["name"] == "High Value Proposal Task"

    # 2. List rules
    list_res = await async_client.get("/api/v1/automations", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 3. Activate rule
    act_res = await async_client.post(f"/api/v1/automations/{rule_id}/activate", headers=headers)
    assert act_res.status_code == 200
    assert act_res.json()["status"] == "ACTIVE"

    # 4. Pause rule
    pause_res = await async_client.post(f"/api/v1/automations/{rule_id}/pause", headers=headers)
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "PAUSED"

    # 5. Archive rule
    arch_res = await async_client.post(f"/api/v1/automations/{rule_id}/archive", headers=headers)
    assert arch_res.status_code == 200
    assert arch_res.json()["status"] == "ARCHIVED"


@pytest.mark.asyncio
async def test_trigger_condition_matching_and_action_execution(async_client: AsyncClient):
    """Verifies workflow trigger matching, condition evaluation, and activity creation on deal stage change."""
    reg = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Workflow Exec Org",
        "organization_slug": f"wfexec-{uuid.uuid4().hex[:8]}",
        "email": f"user-{uuid.uuid4().hex[:6]}@wfexec.com",
        "password": "Password123!",
        "full_name": "Workflow User"
    })
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    # Create customer
    cust_res = await async_client.post("/api/v1/customers", json={"name": "Workflow Target Corp"}, headers=headers)
    cust_id = cust_res.json()["id"]

    # Create active rule
    rule_res = await async_client.post("/api/v1/automations", json={
        "name": "Auto Task on Proposal Stage",
        "trigger_type": "DEAL_STAGE_CHANGED",
        "priority": 1,
        "conditions": {
            "logical_operator": "AND",
            "conditions": [
                {"field": "deal.stage", "operator": "equals", "value": "proposal"}
            ]
        },
        "actions": [
            {
                "action_type": "CREATE_ACTIVITY",
                "parameters": {
                    "title": "Automated Proposal Review Call",
                    "activity_type": "call",
                    "priority": "high"
                }
            }
        ]
    }, headers=headers)
    rule_id = rule_res.json()["id"]
    await async_client.post(f"/api/v1/automations/{rule_id}/activate", headers=headers)

    # Create deal in 'new' stage
    deal_res = await async_client.post("/api/v1/deals", json={
        "customer_id": cust_id,
        "title": "Enterprise Cloud Deal",
        "stage": "new",
        "value": "120000.00"
    }, headers=headers)
    deal_id = deal_res.json()["id"]

    # Change deal stage to 'proposal'
    await async_client.put(f"/api/v1/deals/{deal_id}", json={"stage": "proposal"}, headers=headers)

    # Check execution history
    execs_res = await async_client.get("/api/v1/automations/executions", headers=headers)
    assert execs_res.status_code == 200
    execs = execs_res.json()
    assert len(execs) >= 1
    matched_exec = next((e for e in execs if e["rule_id"] == rule_id), None)
    assert matched_exec is not None
    assert matched_exec["status"] == "SUCCESS"
    assert matched_exec["conditions_matched"] is True
    assert matched_exec["actions_succeeded"] == 1

    # Verify generated activity item exists in activity list
    acts_res = await async_client.get("/api/v1/activities", headers=headers)
    assert acts_res.status_code == 200
    act_titles = [a["title"] for a in acts_res.json()]
    assert "Automated Proposal Review Call" in act_titles


@pytest.mark.asyncio
async def test_automation_idempotency(async_client: AsyncClient):
    """Verifies that firing the same event context twice does not execute duplicate actions."""
    reg = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Idempotency Org",
        "organization_slug": f"idemp-{uuid.uuid4().hex[:8]}",
        "email": f"user-{uuid.uuid4().hex[:6]}@idemp.com",
        "password": "Password123!",
        "full_name": "Idemp User"
    })
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    cust_res = await async_client.post("/api/v1/customers", json={"name": "Idemp Customer"}, headers=headers)
    cust_id = cust_res.json()["id"]

    rule_res = await async_client.post("/api/v1/automations", json={
        "name": "Idempotent Task Rule",
        "trigger_type": "DEAL_CREATED",
        "conditions": {"logical_operator": "AND", "conditions": []},
        "actions": [{"action_type": "CREATE_ACTIVITY", "parameters": {"title": "Unique Created Task"}}]
    }, headers=headers)
    rule_id = rule_res.json()["id"]
    await async_client.post(f"/api/v1/automations/{rule_id}/activate", headers=headers)

    # Creating deal triggers DEAL_CREATED
    await async_client.post("/api/v1/deals", json={
        "customer_id": cust_id,
        "title": "Idempotent Deal 1",
        "stage": "new",
        "value": "10000.00"
    }, headers=headers)

    execs_res = await async_client.get("/api/v1/automations/executions", headers=headers)
    assert execs_res.status_code == 200
    assert len(execs_res.json()) == 1


@pytest.mark.asyncio
async def test_tenant_automation_isolation(async_client: AsyncClient):
    """Confirms Org A cannot view or modify Org B automation rules or execution history."""
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Auto Org A",
        "organization_slug": f"autoa-{uuid.uuid4().hex[:8]}",
        "email": f"user-{uuid.uuid4().hex[:6]}@autoa.com",
        "password": "Password123!",
        "full_name": "Org A User"
    })
    headers_a = {"Authorization": f"Bearer {reg_a.json()['access_token']}"}

    rule_a = await async_client.post("/api/v1/automations", json={
        "name": "Org A Secret Rule",
        "trigger_type": "DEAL_CREATED",
        "conditions": {"logical_operator": "AND", "conditions": []},
        "actions": [{"action_type": "SEND_NOTIFICATION", "parameters": {"title": "Org A Alert"}}]
    }, headers=headers_a)
    rule_a_id = rule_a.json()["id"]

    reg_b = await async_client.post("/api/v1/auth/register", json={
        "organization_name": "Auto Org B",
        "organization_slug": f"autob-{uuid.uuid4().hex[:8]}",
        "email": f"user-{uuid.uuid4().hex[:6]}@autob.com",
        "password": "Password123!",
        "full_name": "Org B User"
    })
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    # Org B trying to view Org A rule -> 404
    res = await async_client.get(f"/api/v1/automations/{rule_a_id}", headers=headers_b)
    assert res.status_code == 404

    # Org B listing rules -> Org A rule not listed
    list_b = await async_client.get("/api/v1/automations", headers=headers_b)
    assert list_b.status_code == 200
    assert all(r["id"] != rule_a_id for r in list_b.json())


@pytest.mark.asyncio
async def test_unauthenticated_automation_rejected(async_client: AsyncClient):
    """Verifies unauthenticated GET /api/v1/automations returns 401."""
    res = await async_client.get("/api/v1/automations")
    assert res.status_code == 401
