import json

import pytest

from pulp_docs.openapi import annotate_api_json


def make_spec(versions: dict | None = None, description: str = "") -> str:
    info: dict = {}
    if description:
        info["description"] = description
    if versions is not None:
        info["x-pulp-app-versions"] = versions
    return json.dumps({"info": info})


@pytest.mark.parametrize(
    "initial_description,versions,expected_description",
    [
        pytest.param(
            "",
            {"core": "3.70"},
            "Generated from: pulpcore 3.70",
            id="no-desc-core-only",
        ),
        pytest.param(
            "",
            {"file": "1.5"},
            "Generated from: pulp_file 1.5",
            id="no-desc-non-core",
        ),
        pytest.param(
            "",
            {"core": "3.70", "file": "1.5"},
            "Generated from: pulp_file 1.5 (pulpcore 3.70)",
            id="no-desc-mixed",
        ),
        pytest.param(
            "Some description.",
            {"core": "3.70"},
            "Some description.\n\nGenerated from: pulpcore 3.70",
            id="existing-desc-core-only",
        ),
        pytest.param(
            "Some description.",
            {"core": "3.70", "file": "1.5"},
            "Some description.\n\nGenerated from: pulp_file 1.5 (pulpcore 3.70)",
            id="existing-desc-mixed",
        ),
    ],
)
def test_annotate(initial_description, versions, expected_description):
    result = json.loads(
        annotate_api_json(make_spec(versions=versions, description=initial_description))
    )
    assert result["info"]["description"] == expected_description
    assert "title" not in result["info"]
