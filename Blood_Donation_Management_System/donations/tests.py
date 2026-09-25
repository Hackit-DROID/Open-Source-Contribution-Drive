"""Unit and integration tests for ABO/Rh blood group compatibility matrix
and donor search filtering in Blood_Donation_Management_System.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from donations.models import Donor
from donations.compatibility import (
    COMPATIBLE_DONOR_TYPES,
    ALL_BLOOD_GROUPS,
    get_compatible_donor_types,
    is_compatible,
    filter_compatible_donors,
)


class BloodCompatibilityMatrixTests(TestCase):
    """Verify ABO/Rh compatibility mapping logic across all 8 blood types."""

    def test_all_eight_blood_groups_defined(self):
        """Ensure all 8 ABO/Rh blood groups are defined in the matrix."""
        expected_groups = {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"}
        self.assertEqual(set(ALL_BLOOD_GROUPS), expected_groups)
        self.assertEqual(set(COMPATIBLE_DONOR_TYPES.keys()), expected_groups)

    def test_o_negative_recipient_compatibility(self):
        """O- recipient can ONLY receive from O- (universal red cell donor)."""
        compatible = get_compatible_donor_types("O-")
        self.assertEqual(compatible, ["O-"])
        self.assertTrue(is_compatible("O-", "O-"))
        self.assertFalse(is_compatible("O+", "O-"))
        self.assertFalse(is_compatible("A+", "O-"))
        self.assertFalse(is_compatible("AB+", "O-"))

    def test_o_positive_recipient_compatibility(self):
        """O+ recipient can receive from O- and O+."""
        compatible = get_compatible_donor_types("O+")
        self.assertEqual(set(compatible), {"O-", "O+"})
        self.assertTrue(is_compatible("O-", "O+"))
        self.assertTrue(is_compatible("O+", "O+"))
        self.assertFalse(is_compatible("A+", "O+"))
        self.assertFalse(is_compatible("B+", "O+"))

    def test_a_negative_recipient_compatibility(self):
        """A- recipient can receive from O- and A-."""
        compatible = get_compatible_donor_types("A-")
        self.assertEqual(set(compatible), {"O-", "A-"})
        self.assertTrue(is_compatible("O-", "A-"))
        self.assertTrue(is_compatible("A-", "A-"))
        self.assertFalse(is_compatible("A+", "A-"))
        self.assertFalse(is_compatible("B-", "A-"))

    def test_a_positive_recipient_compatibility(self):
        """A+ recipient can receive from O-, O+, A-, and A+."""
        compatible = get_compatible_donor_types("A+")
        self.assertEqual(set(compatible), {"O-", "O+", "A-", "A+"})
        self.assertTrue(is_compatible("O-", "A+"))
        self.assertTrue(is_compatible("O+", "A+"))
        self.assertTrue(is_compatible("A-", "A+"))
        self.assertTrue(is_compatible("A+", "A+"))
        self.assertFalse(is_compatible("B+", "A+"))
        self.assertFalse(is_compatible("AB+", "A+"))

    def test_b_negative_recipient_compatibility(self):
        """B- recipient can receive from O- and B-."""
        compatible = get_compatible_donor_types("B-")
        self.assertEqual(set(compatible), {"O-", "B-"})
        self.assertTrue(is_compatible("O-", "B-"))
        self.assertTrue(is_compatible("B-", "B-"))
        self.assertFalse(is_compatible("B+", "B-"))
        self.assertFalse(is_compatible("A-", "B-"))

    def test_b_positive_recipient_compatibility(self):
        """B+ recipient can receive from O-, O+, B-, and B+."""
        compatible = get_compatible_donor_types("B+")
        self.assertEqual(set(compatible), {"O-", "O+", "B-", "B+"})
        self.assertTrue(is_compatible("O-", "B+"))
        self.assertTrue(is_compatible("O+", "B+"))
        self.assertTrue(is_compatible("B-", "B+"))
        self.assertTrue(is_compatible("B+", "B+"))
        self.assertFalse(is_compatible("A+", "B+"))
        self.assertFalse(is_compatible("AB+", "B+"))

    def test_ab_negative_recipient_compatibility(self):
        """AB- recipient can receive from O-, A-, B-, and AB-."""
        compatible = get_compatible_donor_types("AB-")
        self.assertEqual(set(compatible), {"O-", "A-", "B-", "AB-"})
        self.assertTrue(is_compatible("O-", "AB-"))
        self.assertTrue(is_compatible("A-", "AB-"))
        self.assertTrue(is_compatible("B-", "AB-"))
        self.assertTrue(is_compatible("AB-", "AB-"))
        self.assertFalse(is_compatible("O+", "AB-"))
        self.assertFalse(is_compatible("A+", "AB-"))
        self.assertFalse(is_compatible("B+", "AB-"))
        self.assertFalse(is_compatible("AB+", "AB-"))

    def test_ab_positive_recipient_compatibility(self):
        """AB+ recipient is universal recipient, can receive from all 8 blood types."""
        compatible = get_compatible_donor_types("AB+")
        self.assertEqual(set(compatible), set(ALL_BLOOD_GROUPS))
        for donor_type in ALL_BLOOD_GROUPS:
            self.assertTrue(is_compatible(donor_type, "AB+"))

    def test_universal_donor_o_negative(self):
        """O- can donate to every recipient blood type."""
        for recipient_type in ALL_BLOOD_GROUPS:
            self.assertTrue(
                is_compatible("O-", recipient_type),
                f"O- should be compatible with {recipient_type}"
            )

    def test_normalization_and_invalid_inputs(self):
        """Check whitespace trimming, case-insensitivity, and invalid blood types."""
        self.assertEqual(get_compatible_donor_types(" a+ "), ["O-", "O+", "A-", "A+"])
        self.assertEqual(get_compatible_donor_types("o-"), ["O-"])
        self.assertEqual(get_compatible_donor_types(""), [])
        self.assertEqual(get_compatible_donor_types("INVALID"), [])
        self.assertFalse(is_compatible("", "A+"))
        self.assertFalse(is_compatible("A+", ""))


class DonorCompatibilityQuerysetTests(TestCase):
    """Test database filtering of donors by recipient compatibility."""

    def setUp(self):
        self.donors = {}
        for bg in ALL_BLOOD_GROUPS:
            self.donors[bg] = Donor.objects.create(
                name=f"Donor {bg}",
                blood_group=bg,
                contact="1234567890",
                city="TestCity"
            )

    def test_filter_o_negative_recipient(self):
        """O- recipient gets only O- donors."""
        filtered = filter_compatible_donors(Donor.objects.all(), "O-")
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().blood_group, "O-")

    def test_filter_o_positive_recipient(self):
        """O+ recipient gets O- and O+ donors."""
        filtered = filter_compatible_donors(Donor.objects.all(), "O+")
        self.assertEqual(filtered.count(), 2)
        groups = set(filtered.values_list("blood_group", flat=True))
        self.assertEqual(groups, {"O-", "O+"})

    def test_filter_a_positive_recipient(self):
        """A+ recipient gets O-, O+, A-, A+ donors."""
        filtered = filter_compatible_donors(Donor.objects.all(), "A+")
        self.assertEqual(filtered.count(), 4)
        groups = set(filtered.values_list("blood_group", flat=True))
        self.assertEqual(groups, {"O-", "O+", "A-", "A+"})

    def test_filter_ab_positive_recipient(self):
        """AB+ recipient gets all 8 donors."""
        filtered = filter_compatible_donors(Donor.objects.all(), "AB+")
        self.assertEqual(filtered.count(), 8)

    def test_filter_empty_recipient_returns_all(self):
        """Empty recipient query returns unfiltered queryset."""
        filtered = filter_compatible_donors(Donor.objects.all(), "")
        self.assertEqual(filtered.count(), 8)


class DonorListViewCompatibilityIntegrationTests(TestCase):
    """Test HTTP integration and template rendering for donor compatibility filtering."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.client = Client()
        self.client.login(username="testuser", password="password123")

        for bg in ["O-", "O+", "A+", "B+"]:
            Donor.objects.create(name=f"Donor {bg}", blood_group=bg, city="Metropolis")

    def test_donor_list_without_filter_shows_all(self):
        url = reverse("donor_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "donations/donor_list.html")
        self.assertEqual(len(response.context["donors"]), 4)
        self.assertEqual(response.context["selected_recipient"], "")

    def test_donor_list_with_recipient_filter(self):
        url = reverse("donor_list")
        response = self.client.get(url, {"recipient_type": "O+"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_recipient"], "O+")
        self.assertEqual(set(response.context["compatible_types"]), {"O-", "O+"})
        # Should only return O- and O+ donors
        donor_groups = {d.blood_group for d in response.context["donors"]}
        self.assertEqual(donor_groups, {"O-", "O+"})
        self.assertContains(response, "Recipient O+")
        self.assertContains(response, "Showing donors compatible with recipient")
