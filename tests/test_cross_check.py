from app.services.cross_check import CrossCheckService


def test_extract_declared_experience_years() -> None:
    lines = ["Worked on APIs", "5 years experience in backend development"]
    assert CrossCheckService._extract_declared_experience_years(lines) == 5
