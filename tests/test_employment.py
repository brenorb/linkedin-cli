from datetime import date

from linkedin_cli.employment import (
    filter_employment_history,
    normalize_current_position,
    normalize_positions_payload,
)


def test_normalize_positions_payload_maps_profile_api_positions() -> None:
    payload = {
        "positions": {
            "elements": [
                {
                    "companyName": {
                        "localized": {
                            "en_US": "FACTORED",
                        },
                        "preferredLocale": {
                            "country": "US",
                            "language": "en",
                        },
                    },
                    "title": {
                        "localized": {
                            "en_US": "AI Engineer",
                        },
                        "preferredLocale": {
                            "country": "US",
                            "language": "en",
                        },
                    },
                    "startMonthYear": {
                        "month": 1,
                        "year": 2024,
                    },
                },
                {
                    "companyName": {
                        "localized": {
                            "en_US": "Older Co",
                        },
                        "preferredLocale": {
                            "country": "US",
                            "language": "en",
                        },
                    },
                    "title": {
                        "localized": {
                            "en_US": "Engineer",
                        },
                        "preferredLocale": {
                            "country": "US",
                            "language": "en",
                        },
                    },
                    "startMonthYear": {
                        "month": 1,
                        "year": 2018,
                    },
                    "endMonthYear": {
                        "month": 12,
                        "year": 2019,
                    },
                },
            ]
        }
    }

    records = normalize_positions_payload(payload)

    assert records == [
        {
            "employer_name": "FACTORED",
            "job_title": "AI Engineer",
            "start_date": "2024-01",
            "end_date": None,
            "is_current": True,
        },
        {
            "employer_name": "Older Co",
            "job_title": "Engineer",
            "start_date": "2018-01",
            "end_date": "2019-12",
            "is_current": False,
        },
    ]


def test_filter_employment_history_keeps_only_previous_five_years() -> None:
    records = [
        {
            "employer_name": "FACTORED",
            "job_title": "AI Engineer",
            "start_date": "2024-01",
            "end_date": None,
            "is_current": True,
        },
        {
            "employer_name": "Recent Co",
            "job_title": "Engineer",
            "start_date": "2021-06",
            "end_date": "2023-12",
            "is_current": False,
        },
        {
            "employer_name": "Old Co",
            "job_title": "Intern",
            "start_date": "2018-01",
            "end_date": "2019-12",
            "is_current": False,
        },
    ]

    filtered = filter_employment_history(records, years=5, today=date(2026, 6, 15))

    assert filtered == [
        {
            "employer_name": "FACTORED",
            "job_title": "AI Engineer",
            "start_date": "2024-01",
            "end_date": None,
            "is_current": True,
        },
        {
            "employer_name": "Recent Co",
            "job_title": "Engineer",
            "start_date": "2021-06",
            "end_date": "2023-12",
            "is_current": False,
        },
    ]


def test_normalize_current_position_maps_identity_me_response() -> None:
    payload = {
        "primaryCurrentPosition": {
            "title": {
                "localized": {
                    "en_US": "Senior Software Engineer",
                },
                "preferredLocale": {
                    "country": "US",
                    "language": "en",
                },
            },
            "companyName": {
                "localized": {
                    "en_US": "LinkedIn",
                },
                "preferredLocale": {
                    "country": "US",
                    "language": "en",
                },
            },
            "startedOn": {
                "month": 1,
                "year": 2022,
            },
        }
    }

    assert normalize_current_position(payload) == [
        {
            "employer_name": "LinkedIn",
            "job_title": "Senior Software Engineer",
            "start_date": "2022-01",
            "end_date": None,
            "is_current": True,
        }
    ]
