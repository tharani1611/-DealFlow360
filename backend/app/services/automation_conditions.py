from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from app.schemas.automation import AutomationCondition, AutomationConditionGroup


def resolve_field_value(context: Dict[str, Any], field_path: str) -> Any:
    """Safely extracts field value from structured event context or entity dict using dot notation."""
    if not field_path:
        return None

    parts = field_path.split(".")

    # 1. Direct path lookup
    curr: Any = context
    found = True
    for part in parts:
        if isinstance(curr, dict) and part in curr:
            curr = curr[part]
        elif hasattr(curr, part):
            curr = getattr(curr, part)
        else:
            found = False
            break

    if found and curr is not None:
        return curr

    # 2. Check inside context["payload"] e.g. payload -> deal -> stage
    payload = context.get("payload")
    if isinstance(payload, dict):
        curr = payload
        found = True
        for part in parts:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            elif hasattr(curr, part):
                curr = getattr(curr, part)
            else:
                found = False
                break
        if found and curr is not None:
            return curr

    # 3. Check inside context["current_state"]
    curr_state = context.get("current_state")
    if isinstance(curr_state, dict):
        key = parts[-1]
        if key in curr_state and curr_state[key] is not None:
            return curr_state[key]

    return None


def evaluate_single_condition(context: Dict[str, Any], cond: AutomationCondition) -> bool:
    """Evaluates a single deterministic condition against event context."""
    val = resolve_field_value(context, cond.field)
    target = cond.value
    op = cond.operator.lower()

    if op == "is_empty":
        return val is None or val == "" or val == [] or val == {}
    elif op == "is_not_empty":
        return val is not None and val != "" and val != [] and val != {}

    if val is None:
        return False

    # Convert numeric strings / floats / Decimals if both sides are numbers
    try:
        if isinstance(target, (int, float, str, Decimal)) and isinstance(val, (int, float, str, Decimal)):
            # Check if numeric conversion is appropriate
            str_val = str(val).strip()
            str_target = str(target).strip() if target is not None else ""
            if (str_val.replace('.', '', 1).isdigit() or (str_val.startswith('-') and str_val[1:].replace('.', '', 1).isdigit())) and \
               (str_target.replace('.', '', 1).isdigit() or (str_target.startswith('-') and str_target[1:].replace('.', '', 1).isdigit())):
                val_num = Decimal(str_val)
                target_num = Decimal(str_target)
                if op == "equals":
                    return val_num == target_num
                elif op == "not_equals":
                    return val_num != target_num
                elif op in ("greater_than", "gt"):
                    return val_num > target_num
                elif op in ("greater_than_or_equal", "gte"):
                    return val_num >= target_num
                elif op in ("less_than", "lt"):
                    return val_num < target_num
                elif op in ("less_than_or_equal", "lte"):
                    return val_num <= target_num
    except Exception:
        pass

    # String & General equality handling
    str_val = str(val).lower() if isinstance(val, str) else val
    str_target = str(target).lower() if isinstance(target, str) else target

    if op == "equals":
        return str_val == str_target
    elif op == "not_equals":
        return str_val != str_target
    elif op == "contains":
        return str_target in str_val if isinstance(str_val, (str, list, dict)) else False
    elif op == "not_contains":
        return str_target not in str_val if isinstance(str_val, (str, list, dict)) else True
    elif op == "in":
        if isinstance(target, list):
            target_list = [str(x).lower() if isinstance(x, str) else x for x in target]
            return str_val in target_list
        return str_val in str_target if isinstance(str_target, (str, list, dict)) else False
    elif op == "not_in":
        if isinstance(target, list):
            target_list = [str(x).lower() if isinstance(x, str) else x for x in target]
            return str_val not in target_list
        return str_val not in str_target if isinstance(str_target, (str, list, dict)) else True
    elif op in ("greater_than", "gt"):
        return val > target
    elif op in ("greater_than_or_equal", "gte"):
        return val >= target
    elif op in ("less_than", "lt"):
        return val < target
    elif op in ("less_than_or_equal", "lte"):
        return val <= target

    return False


def evaluate_condition_group(context: Dict[str, Any], group: Union[AutomationConditionGroup, dict]) -> bool:
    """Recursively evaluates a condition group using AND/OR logic."""
    if isinstance(group, dict):
        group_obj = AutomationConditionGroup(**group)
    else:
        group_obj = group

    logical_op = (group_obj.logical_operator or "AND").upper()

    # Base case: if group is empty, return True
    if not group_obj.conditions and not group_obj.groups:
        return True

    results: List[bool] = []

    for cond in group_obj.conditions:
        if isinstance(cond, dict):
            cond_obj = AutomationCondition(**cond)
        else:
            cond_obj = cond
        results.append(evaluate_single_condition(context, cond_obj))

    for sub_group in group_obj.groups:
        results.append(evaluate_condition_group(context, sub_group))

    if not results:
        return True

    if logical_op == "OR":
        return any(results)
    else:
        return all(results)
