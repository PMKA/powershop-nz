"""Tests for custom_components/powershop_nz/rates.py. Run: python3 -m unittest discover tests"""
import importlib.util
import pathlib
import unittest

# Load rates.py directly: importing the package would pull in Home Assistant.
_PATH = pathlib.Path(__file__).parents[1] / "custom_components" / "powershop_nz" / "rates.py"
_spec = importlib.util.spec_from_file_location("rates", _PATH)
rates = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rates)


def band(rate, category="CONSUMPTION_CHARGE", bucket=""):
    return {"rate": rate, "rate_formatted": f"${rate / 100:.4f}", "band_category": category, "tou_bucket": bucket}


# Shape of a real Unison (Rotorua) agreement as returned by the API, keyed by displayLabel.
UNISON = {
    "Daily Charge": band(264.5, "STANDING_CHARGE"),
    "Night": band(21.28, bucket="N8"),
    "Controlled": band(24.84),
    "Off Peak": band(33.47, bucket="OPK8"),
    "Peak": band(36.92, bucket="PK8"),
}
UNISON_TOU = [{"name": "ST26", "timeslots": [
    {"timeslot": "N8", "activeFrom": "00:00:00", "activeTo": "07:00:00", "weekdays": False, "weekends": False},
    {"timeslot": "N8", "activeFrom": "23:00:00", "activeTo": "00:00:00", "weekdays": False, "weekends": False},
    {"timeslot": "PK8", "activeFrom": "07:00:00", "activeTo": "11:00:00", "weekdays": True, "weekends": False},
    {"timeslot": "OPK8", "activeFrom": "11:00:00", "activeTo": "17:00:00", "weekdays": True, "weekends": False},
    {"timeslot": "PK8", "activeFrom": "17:00:00", "activeTo": "21:00:00", "weekdays": True, "weekends": False},
    {"timeslot": "OPK8", "activeFrom": "21:00:00", "activeTo": "23:00:00", "weekdays": True, "weekends": False},
    {"timeslot": "OPK8", "activeFrom": "07:00:00", "activeTo": "23:00:00", "weekdays": False, "weekends": True},
]}]

# Band names reported for Orion's Get Shifty plan in issue #14 (prices made up).
ORION = {
    "Daily Charge": band(200.0, "STANDING_CHARGE"),
    "Peak": band(40.0), "Shoulder": band(30.0), "Off Peak": band(25.0),
    "Super Off Peak": band(15.0), "Weekend": band(22.0),
}


class RateKey(unittest.TestCase):
    def test_slugs(self):
        self.assertEqual(rates.rate_key("Off Peak"), "rate_off_peak")
        self.assertEqual(rates.rate_key("Super Off-Peak"), "rate_super_off_peak")
        self.assertEqual(rates.rate_key("  Night  "), "rate_night")

    def test_empty_label(self):
        self.assertEqual(rates.rate_key(""), "rate_unnamed")
        self.assertEqual(rates.rate_key("---"), "rate_unnamed")


class ConsumptionRates(unittest.TestCase):
    def test_unison(self):
        got = rates.consumption_rates(UNISON)
        self.assertEqual(set(got), {"rate_night", "rate_controlled", "rate_off_peak", "rate_peak"})
        self.assertEqual(got["rate_night"]["rate"], 21.28)
        self.assertEqual(got["rate_off_peak"]["name"], "Off Peak")

    def test_orion_five_bands(self):
        self.assertEqual(set(rates.consumption_rates(ORION)), {
            "rate_peak", "rate_shoulder", "rate_off_peak", "rate_super_off_peak", "rate_weekend"})

    def test_standing_by_keyword_when_category_missing(self):
        got = rates.consumption_rates({"Daily Charge": {"rate": 1.0}, "Anytime": {"rate": 30.0}})
        self.assertEqual(set(got), {"rate_anytime"})

    def test_collisions_get_stable_suffixes(self):
        periods = {"Off-Peak": band(1.0), "Off Peak": band(2.0)}
        first = rates.consumption_rates(periods)
        again = rates.consumption_rates(dict(reversed(list(periods.items()))))
        self.assertEqual(set(first), {"rate_off_peak", "rate_off_peak_2"})
        self.assertEqual({k: v["rate"] for k, v in first.items()}, {k: v["rate"] for k, v in again.items()})

    def test_empty(self):
        self.assertEqual(rates.consumption_rates({}), {})


class ActiveTimes(unittest.TestCase):
    def test_night_every_day(self):
        # Neither weekdays nor weekends set means every day.
        self.assertEqual(rates.active_times(UNISON_TOU, "N8"), ["Every day 00:00-07:00", "Every day 23:00-00:00"])

    def test_peak_weekdays(self):
        self.assertEqual(rates.active_times(UNISON_TOU, "PK8"), ["Weekdays 07:00-11:00", "Weekdays 17:00-21:00"])

    def test_off_peak_mixed(self):
        self.assertEqual(rates.active_times(UNISON_TOU, "OPK8"),
                         ["Weekdays 11:00-17:00", "Weekdays 21:00-23:00", "Weekends 07:00-23:00"])

    def test_no_bucket(self):
        self.assertEqual(rates.active_times(UNISON_TOU, ""), [])
        self.assertEqual(rates.active_times(UNISON_TOU, None), [])
        self.assertEqual(rates.active_times([], "N8"), [])


if __name__ == "__main__":
    unittest.main()
