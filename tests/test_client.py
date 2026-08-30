"""
Tests for the LinkedIn Voyager client.

Run offline parsing tests (no network):
    pytest tests/test_client.py::test_parse_synthetic -q

Run the live auth gate (requires .env with real burner cookies + network):
    pytest tests/test_client.py::test_live_gate -q
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from linkedin_scraper import LinkedInVoyagerClient  # noqa: E402


# ---------------------------------------------------------------------------
# Offline: verify the flat `included[]` extraction logic against a synthetic
# Voyager-shaped payload. No cookies, no network.
# ---------------------------------------------------------------------------
def _synthetic_dash() -> dict:
    return {
        "included": [
            {
                "entityUrn": "urn:li:fsd_profile:AB00",
                "firstName": "Ada",
                "lastName": "Lovelace",
                "headline": "Mathematician",
                "locationName": "London",
                "industryName": "Software",
                "publicIdentifier": "ada",
                "summary": "First programmer.",
                "profilePicture": {},
            },
            {"$type": "com.linkedin.voyager.identity.profile.Position",
             "title": "Engineer", "companyName": "Analytical Engine",
             "dateRange": {"start": {"year": 1833}}},
            {"$type": "com.linkedin.voyager.identity.profile.Position",
             "title": "Consultant", "companyName": "X",
             "dateRange": {"start": {"year": 1840}, "end": {"year": 1842}}},
            {"$type": "com.linkedin.voyager.identity.profile.Education",
             "schoolName": "Uni", "degreeName": "BS"},
            {"$type": "com.linkedin.voyager.identity.profile.Skill",
             "name": "Math", "endorsementCount": 12},
            {"$type": "com.linkedin.voyager.identity.profile.Certification",
             "name": "Cert"},
            {"$type": "com.linkedin.voyager.identity.profile.Language",
             "name": "English", "proficiency": "Native"},
        ]
    }


def test_parse_synthetic(monkeypatch):
    # Build a client without triggering a real request path: monkeypatch _fetch.
    client = LinkedInVoyagerClient(li_at="x", jsessionid="ajax:1")
    monkeypatch.setattr(client, "_fetch_dash", lambda slug: _patch_included(_synthetic_dash()))
    monkeypatch.setattr(client, "_fetch_contact", lambda slug: {})
    out = client.get_profile("ada")

    assert out["basic"]["full_name"] == "Ada Lovelace"
    assert out["basic"]["headline"] == "Mathematician"
    assert out["about"] == "First programmer."
    # current position has no end date
    assert out["experience"][0]["is_current"] is True
    assert out["experience"][1]["end_date"] != "Present"
    assert out["education"][0]["school"] == "Uni"
    assert out["skills"][0]["name"] == "Math"
    assert out["certifications"][0]["name"] == "Cert"
    assert out["languages"][0]["language"] == "English"


def _patch_included(dash: dict) -> dict:
    prof = next(i for i in dash["included"] if "fsd_profile:" in i["entityUrn"])
    prof = dict(prof)
    prof["_included"] = dash["included"]
    return prof


def test_slug_normalization():
    client = LinkedInVoyagerClient(li_at="x", jsessionid="ajax:1")
    assert client._normalize_slug("https://www.linkedin.com/in/satyanadella/") == "satyanadella"
    assert client._normalize_slug("satyanadella") == "satyanadella"


# ---------------------------------------------------------------------------
# Live gate (network + real burner cookies in .env)
# ---------------------------------------------------------------------------
def test_live_gate():
    env = {}
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    if not env.get("LI_AT_COOKIE") or not env.get("JSESSIONID_COOKIE"):
        pytest.skip("no .env cookies; skipping live gate")

    client = LinkedInVoyagerClient(li_at=env["LI_AT_COOKIE"], jsessionid=env["JSESSIONID_COOKIE"])
    out = client.get_profile("satyanadella")
    assert out["basic"]["full_name"]
    assert "CEO" in out["basic"]["headline"] or out["basic"]["headline"]
