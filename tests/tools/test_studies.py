import json

import httpx

from src.tools.studies import (
    SEARCH_STUDIES_TOOL,
    as_tool_result,
    build_query,
    clean_abstract,
    search_studies,
    strongest_study_type,
)

# Shape of a Europe PMC "core" search response, trimmed to the fields we use.
SAMPLE_RESPONSE = {
    "hitCount": 2,
    "resultList": {
        "result": [
            {
                "id": "11111111",
                "source": "MED",
                "pmid": "11111111",
                "title": "Topical niacinamide for acne: a randomized trial. ",
                "authorString": "Smith A, Jones B.",
                "journalInfo": {"journal": {"title": "J Dermatol"}},
                "pubYear": "2021",
                "pubTypeList": {
                    "pubType": ["Journal Article", "Randomized Controlled Trial"]
                },
                "abstractText": "<h4>Background</h4>Niacinamide   reduced lesions.",
                "isOpenAccess": "Y",
                "citedByCount": 12,
            },
            {
                "id": "PMC999",
                "source": "PMC",
                "title": "A review without a PMID",
                "pubYear": "n/a",
                "pubTypeList": {"pubType": "Review"},
            },
        ]
    },
}


def _client(captured):
    def handler(request):
        captured.append(request)
        return httpx.Response(200, json=SAMPLE_RESPONSE)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_search_studies_parses_results():
    captured = []
    studies = search_studies("niacinamide", "acne", client=_client(captured))

    first = studies[0]
    assert first.title == "Topical niacinamide for acne: a randomized trial."
    assert first.study_type == "randomized controlled trial"
    assert first.journal == "J Dermatol"
    assert first.year == 2021
    assert first.abstract == "Background Niacinamide reduced lesions."
    assert first.url == "https://pubmed.ncbi.nlm.nih.gov/11111111/"
    assert first.open_access is True
    assert first.cited_by == 12

    # Missing fields don't crash, and records without a PMID link to Europe PMC
    second = studies[1]
    assert second.year is None
    assert second.study_type == "review"
    assert second.url == "https://europepmc.org/article/PMC/PMC999"


def test_search_studies_sends_query_and_limit():
    captured = []
    search_studies("retinol", limit=3, client=_client(captured))

    params = captured[0].url.params
    assert params["pageSize"] == "3"
    assert params["resultType"] == "core"
    assert params["query"].startswith('TITLE_ABS:"retinol" AND SRC:MED AND (')


def test_build_query_without_clinical_filter():
    assert build_query("niacinamide", "acne", clinical_only=False) == (
        'TITLE_ABS:"niacinamide" AND TITLE_ABS:"acne" AND SRC:MED'
    )


def test_strongest_study_type_prefers_meta_analysis():
    types = ["Journal Article", "Randomized Controlled Trial", "Meta-Analysis"]
    assert strongest_study_type(types) == "meta-analysis"
    assert strongest_study_type(["Journal Article"]) == "other"


def test_clean_abstract_trims_long_text():
    text = "word " * 500
    cleaned = clean_abstract(text, max_chars=50)
    assert len(cleaned) <= 54
    assert cleaned.endswith(" ...")


def test_tool_result_is_json_and_schema_names_the_tool():
    studies = search_studies("niacinamide", client=_client([]))
    payload = json.loads(as_tool_result(studies))
    assert payload[0]["pmid"] == "11111111"
    assert SEARCH_STUDIES_TOOL["function"]["name"] == "search_studies"
    assert SEARCH_STUDIES_TOOL["function"]["parameters"]["required"] == ["ingredient"]
