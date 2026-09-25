"""Unit tests for Regional Blood Bank Stock Inventory Balancing Engine (CR-752)."""

import unittest

from donations.stock_balancing import (
    FacilityStock,
    RegionalStockBalancingEngine,
    TransferRecommendation,
)


class TestRegionalStockBalancingEngine(unittest.TestCase):
    """Test suite verifying target stock calculation, threshold detection, and transfer recommendations."""

    def setUp(self):
        self.engine = RegionalStockBalancingEngine()

    def test_target_reserve_stock_calculation(self):
        """Target stock should be ceil(avg_weekly_consumption * buffer_weeks)."""
        # 12.4 weekly consumption -> ceil(12.4) = 13
        f1 = FacilityStock(
            facility_id="FAC-1",
            facility_name="Central Hospital",
            blood_group="O+",
            current_stock=20,
            avg_weekly_consumption=12.4,
        )
        self.assertEqual(f1.target_reserve_stock, 13)

        # 0 consumption should yield 0 target
        f2 = FacilityStock(
            facility_id="FAC-2",
            facility_name="Inactive Clinic",
            blood_group="O-",
            current_stock=5,
            avg_weekly_consumption=0.0,
        )
        self.assertEqual(f2.target_reserve_stock, 0)

        # Explicit target stock overrides automatic calculation
        f3 = FacilityStock(
            facility_id="FAC-3",
            facility_name="Custom Base",
            blood_group="A+",
            current_stock=10,
            avg_weekly_consumption=5.0,
            target_reserve_stock=25,
        )
        self.assertEqual(f3.target_reserve_stock, 25)

    def test_surplus_and_deficit_threshold_detection(self):
        """Facilities with >150% target are surplus; <50% target are deficit."""
        # Target = 20. Surplus threshold > 30 (150%). Deficit threshold < 10 (50%).
        surplus_fac = FacilityStock(
            facility_id="FAC-SUR",
            facility_name="Metropolitan Blood Bank",
            blood_group="O-",
            current_stock=35,  # 35 > 30 -> Surplus
            avg_weekly_consumption=20.0,
        )
        self.assertEqual(surplus_fac.target_reserve_stock, 20)
        self.assertEqual(surplus_fac.surplus_threshold, 30.0)
        self.assertTrue(surplus_fac.is_surplus)
        self.assertFalse(surplus_fac.is_deficit)
        self.assertEqual(surplus_fac.transferable_surplus, 15)  # 35 - 20 = 15

        deficit_fac = FacilityStock(
            facility_id="FAC-DEF",
            facility_name="Rural District Hospital",
            blood_group="O-",
            current_stock=8,  # 8 < 10 -> Deficit
            avg_weekly_consumption=20.0,
        )
        self.assertEqual(deficit_fac.deficit_threshold, 10.0)
        self.assertTrue(deficit_fac.is_deficit)
        self.assertFalse(deficit_fac.is_surplus)
        self.assertEqual(deficit_fac.deficit_amount, 12)  # 20 - 8 = 12

        # Balanced stock (e.g. 25 units for target 20) is neither surplus nor deficit
        normal_fac = FacilityStock(
            facility_id="FAC-NORM",
            facility_name="Community Clinic",
            blood_group="O-",
            current_stock=25,
            avg_weekly_consumption=20.0,
        )
        self.assertFalse(normal_fac.is_surplus)
        self.assertFalse(normal_fac.is_deficit)
        self.assertEqual(normal_fac.transferable_surplus, 0)
        self.assertEqual(normal_fac.deficit_amount, 0)

    def test_identify_surplus_and_deficit_facilities(self):
        """Engine correctly identifies and sorts surplus and deficit facilities."""
        fac_surplus1 = FacilityStock(
            facility_id="F1", facility_name="Hub East", blood_group="A+",
            current_stock=50, avg_weekly_consumption=20.0  # target 20, surplus = 30
        )
        fac_surplus2 = FacilityStock(
            facility_id="F2", facility_name="Hub West", blood_group="A+",
            current_stock=35, avg_weekly_consumption=20.0  # target 20, surplus = 15
        )
        fac_deficit = FacilityStock(
            facility_id="F3", facility_name="Outpost North", blood_group="A+",
            current_stock=4, avg_weekly_consumption=20.0   # target 20, deficit = 16
        )

        self.engine.register_facility_stock(fac_surplus1)
        self.engine.register_facility_stock(fac_surplus2)
        self.engine.register_facility_stock(fac_deficit)

        surplus = self.engine.identify_surplus_facilities(blood_group="A+")
        deficits = self.engine.identify_deficit_facilities(blood_group="A+")

        self.assertEqual([f.facility_id for f in surplus], ["F1", "F2"])
        self.assertEqual([f.facility_id for f in deficits], ["F3"])

    def test_generate_transfer_recommendations_balances_inventory(self):
        """Engine pairs surplus with deficit to generate precise transfer recommendations."""
        # F1 has 40 units (target 20, surplus = 20)
        # F2 has 5 units (target 20, deficit = 15)
        f1 = FacilityStock(
            facility_id="F1", facility_name="Central Reserve", blood_group="B+",
            current_stock=40, avg_weekly_consumption=20.0
        )
        f2 = FacilityStock(
            facility_id="F2", facility_name="St. Jude Urgent", blood_group="B+",
            current_stock=5, avg_weekly_consumption=20.0
        )

        self.engine.register_facility_stock(f1)
        self.engine.register_facility_stock(f2)

        transfers = self.engine.generate_transfer_recommendations(blood_group="B+")
        self.assertEqual(len(transfers), 1)

        transfer = transfers[0]
        self.assertEqual(transfer.from_facility_id, "F1")
        self.assertEqual(transfer.to_facility_id, "F2")
        self.assertEqual(transfer.blood_group, "B+")
        # Should transfer exactly the deficit amount: 15 units
        self.assertEqual(transfer.units, 15)
        self.assertIn("Rebalance regional B+ supply", transfer.rationale)

    def test_multi_facility_transfer_allocation(self):
        """When multiple surplus facilities exist, orders distribute appropriately."""
        # Deficit facility needs 25 units
        # F_surplus1 has 10 transferable units
        # F_surplus2 has 20 transferable units
        f_def = FacilityStock(
            facility_id="F_DEF", facility_name="Valley Hospital", blood_group="AB-",
            current_stock=5, avg_weekly_consumption=30.0  # target 30, deficit 25
        )
        f_sur1 = FacilityStock(
            facility_id="F_SUR1", facility_name="City Center", blood_group="AB-",
            current_stock=40, avg_weekly_consumption=20.0  # target 20, transferable 20
        )
        f_sur2 = FacilityStock(
            facility_id="F_SUR2", facility_name="Port Infirmary", blood_group="AB-",
            current_stock=35, avg_weekly_consumption=20.0  # target 20, transferable 15
        )

        self.engine.register_facility_stock(f_def)
        self.engine.register_facility_stock(f_sur1)
        self.engine.register_facility_stock(f_sur2)

        transfers = self.engine.generate_transfer_recommendations(blood_group="AB-")
        # Deficit of 25 should be satisfied by F_SUR1 (20 units) and F_SUR2 (5 units)
        total_transferred = sum(t.units for t in transfers)
        self.assertEqual(total_transferred, 25)
        self.assertEqual(len(transfers), 2)
        self.assertEqual(transfers[0].units, 20)
        self.assertEqual(transfers[1].units, 5)


if __name__ == "__main__":
    unittest.main()
