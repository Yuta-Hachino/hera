"""Shared validation helpers for Hera user profiles."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Union


ProfileLike = Union[Dict[str, Any], "UserProfile"]  # pyright: ignore[reportUndefinedVariable]


PROFILE_BASE_REQUIRED_FIELDS: List[str] = [
    "age",
    "gender",
    "relationship_status",
    "location",
    "income_range",
    "user_personality_traits",
    "partner_face_description",
    "children_info",
]


RELATIONSHIP_REQUIRED_FIELDS: Dict[str, Sequence[str]] = {
    "married": ["current_partner"],
    "partnered": ["current_partner"],
    "single": ["ideal_partner"],
    "other": ["ideal_partner"],
}


BIG_FIVE_KEYS: Sequence[str] = (
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
)


USER_PERSONALITY_MIN_TRAITS = 2


PARTNER_APPEARANCE_KEYS: Sequence[str] = (
    "appearance",
    "face_description",
    "visual_traits",
)


def _ensure_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _ensure_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    return []


def _as_profile_dict(profile: ProfileLike) -> Dict[str, Any]:
    if hasattr(profile, "dict") and callable(getattr(profile, "dict")):
        return dict(getattr(profile, "dict")())
    return dict(profile) if isinstance(profile, dict) else {}


def is_value_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, tuple, set, dict)) and len(value) == 0:
        return True
    return False


def _is_personality_complete(personality: Any) -> bool:
    data = _ensure_dict(personality)
    if not data:
        return False
    filled = sum(1 for key in BIG_FIVE_KEYS if not is_value_missing(data.get(key)))
    return filled >= USER_PERSONALITY_MIN_TRAITS


def _is_partner_complete(partner: Any) -> bool:
    data = _ensure_dict(partner)
    if not data:
        return False
    if is_value_missing(data.get("temperament")):
        return False
    if not any(not is_value_missing(data.get(name)) for name in PARTNER_APPEARANCE_KEYS):
        return False
    # パートナーの名前を必須にする
    if is_value_missing(data.get("name")):
        return False
    return True


def _is_children_complete(children: Any) -> bool:
    items = _ensure_list(children)
    if not items:
        return False
    for item in items:
        if isinstance(item, dict):
            # 子供の性別と名前の両方が必須
            if (not is_value_missing(item.get("desired_gender")) and
                not is_value_missing(item.get("name"))):
                return True
        elif not is_value_missing(item):
            return True
    return False


def field_is_complete(field: str, profile: ProfileLike) -> bool:
    profile_dict = _as_profile_dict(profile)
    value = profile_dict.get(field)

    if field == "user_personality_traits":
        return _is_personality_complete(value)
    if field == "children_info":
        return _is_children_complete(value)
    if field in ("ideal_partner", "current_partner"):
        return _is_partner_complete(value)
    if field == "partner_face_description":
        return not is_value_missing(value)
    return not is_value_missing(value)


def build_information_progress(profile: ProfileLike) -> Dict[str, bool]:
    profile_dict = _as_profile_dict(profile)
    progress: Dict[str, bool] = {}

    for field in PROFILE_BASE_REQUIRED_FIELDS:
        progress[field] = field_is_complete(field, profile_dict)

    relationship = profile_dict.get("relationship_status")
    for field in RELATIONSHIP_REQUIRED_FIELDS.get(relationship, []):
        progress[field] = field_is_complete(field, profile_dict)

    return progress


def compute_missing_fields(profile: ProfileLike) -> List[str]:
    profile_dict = _as_profile_dict(profile)
    missing: List[str] = []

    for field in PROFILE_BASE_REQUIRED_FIELDS:
        if not field_is_complete(field, profile_dict):
            missing.append(field)

    relationship = profile_dict.get("relationship_status")
    for field in RELATIONSHIP_REQUIRED_FIELDS.get(relationship, []):
        if not field_is_complete(field, profile_dict):
            missing.append(field)

    return missing


def collect_missing_field_details(profile: ProfileLike) -> List[str]:
    profile_dict = _as_profile_dict(profile)
    details: List[str] = []

    if not field_is_complete("user_personality_traits", profile_dict):
        data = _ensure_dict(profile_dict.get("user_personality_traits"))
        filled = [key for key in BIG_FIVE_KEYS if not is_value_missing(data.get(key))]
        missing_needed = max(0, USER_PERSONALITY_MIN_TRAITS - len(filled))
        for key in BIG_FIVE_KEYS:
            if missing_needed <= 0:
                break
            if is_value_missing(data.get(key)):
                details.append(f"user_personality_traits.{key}")
                missing_needed -= 1

    for partner_field in ("ideal_partner", "current_partner"):
        if not field_is_complete(partner_field, profile_dict):
            data = _ensure_dict(profile_dict.get(partner_field))
            if is_value_missing(data.get("temperament")):
                details.append(f"{partner_field}.temperament")
            if not any(not is_value_missing(data.get(name)) for name in PARTNER_APPEARANCE_KEYS):
                details.append(f"{partner_field}.appearance")

    if not field_is_complete("children_info", profile_dict):
        details.append("children_info")

    return details


def profile_is_complete(profile: ProfileLike) -> bool:
    return len(compute_missing_fields(profile)) == 0


def prune_empty_fields(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            pruned = prune_empty_fields(value)
            if not is_value_missing(pruned):
                cleaned[key] = pruned
        return cleaned
    if isinstance(data, list):
        cleaned_list = [prune_empty_fields(item) for item in data]
        return [item for item in cleaned_list if not is_value_missing(item)]
    return data


__all__ = [
    "BIG_FIVE_KEYS",
    "PROFILE_BASE_REQUIRED_FIELDS",
    "RELATIONSHIP_REQUIRED_FIELDS",
    "collect_missing_field_details",
    "compute_missing_fields",
    "field_is_complete",
    "is_value_missing",
    "profile_is_complete",
    "build_information_progress",
    "prune_empty_fields",
]
