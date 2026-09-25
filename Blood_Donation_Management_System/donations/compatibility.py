"""ABO/Rh Blood Group Compatibility Matrix and Search Utilities.

Provides red blood cell transfusion compatibility mapping and donor filtering
based on recipient ABO/Rh blood types.
"""

from typing import Dict, List, Optional


# Red blood cell donor compatibility mapping: recipient -> list of compatible donor groups
COMPATIBLE_DONOR_TYPES: Dict[str, List[str]] = {
    "O-": ["O-"],
    "O+": ["O-", "O+"],
    "A-": ["O-", "A-"],
    "A+": ["O-", "O+", "A-", "A+"],
    "B-": ["O-", "B-"],
    "B+": ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
}

# All standard 8 ABO/Rh blood group categories
ALL_BLOOD_GROUPS: List[str] = [
    "O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"
]


def get_compatible_donor_types(recipient_type: str) -> List[str]:
    """Retrieve all compatible donor blood types for a given recipient ABO/Rh blood group.

    Args:
        recipient_type: The recipient's blood group (e.g. 'O-', 'A+', 'AB+').

    Returns:
        List of compatible donor blood types. Returns empty list if invalid or unrecognized.
    """
    if not recipient_type or not isinstance(recipient_type, str):
        return []
    normalized = recipient_type.strip().upper()
    return COMPATIBLE_DONOR_TYPES.get(normalized, [])


def is_compatible(donor_type: str, recipient_type: str) -> bool:
    """Verify if a donor blood group can donate to a recipient blood group.

    Args:
        donor_type: ABO/Rh blood group of the donor.
        recipient_type: ABO/Rh blood group of the recipient.

    Returns:
        True if the transfusion combination is compatible, False otherwise.
    """
    if not donor_type or not recipient_type:
        return False
    d = donor_type.strip().upper()
    compatible_donors = get_compatible_donor_types(recipient_type)
    return d in compatible_donors


def filter_compatible_donors(queryset, recipient_type: str):
    """Filter a Donor queryset by blood types compatible with the recipient.

    Args:
        queryset: Django queryset of Donor objects.
        recipient_type: Target recipient blood group string.

    Returns:
        Filtered queryset matching compatible donor blood groups.
    """
    if not recipient_type:
        return queryset

    compatible_types = get_compatible_donor_types(recipient_type)
    if compatible_types:
        return queryset.filter(blood_group__in=compatible_types)

    # Fallback to exact match if an unrecognized custom group is provided
    return queryset.filter(blood_group=recipient_type.strip().upper())
