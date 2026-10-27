"""search_studies: find clinical studies about a skincare ingredient.

Uses the Europe PMC REST API (free, no key), which indexes PubMed. This module is
plain Python: the model does not call it yet. It also defines the tool schema the
model will see once the tool-calling loop is added.
"""

import json
import re
import sys
from dataclasses import asdict, dataclass
from typing import List, Optional

import httpx

EUROPE_PMC_SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


class StudySearchError(Exception):
    """Europe PMC could not be reached or answered badly. The message is safe to show."""


# Strongest evidence first. Used to label each study with its best publication type.
STUDY_TYPE_RANKING = [
    "meta-analysis",
    "systematic review",
    "randomized controlled trial",
    "clinical trial",
    "review",
]
CLINICAL_TYPES = STUDY_TYPE_RANKING[:4]

# Keep tool results small: the abstract is trimmed before it reaches the model.
MAX_ABSTRACT_CHARS = 1200

SEARCH_STUDIES_TOOL = {
    "type": "function",
    "function": {
        "name": "search_studies",
        "description": (
            "Search published clinical studies (PubMed via Europe PMC) about a "
            "skincare ingredient, optionally for a specific skin concern. Use it "
            "when the user asks whether an ingredient works or is safe. Returns "
            "titles, study type, year, a short abstract and a link for citing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ingredient": {
                    "type": "string",
                    "description": "INCI or common name, e.g. 'niacinamide'.",
                },
                "concern": {
                    "type": "string",
                    "description": "Optional skin concern, e.g. 'acne'.",
                },
            },
            "required": ["ingredient"],
        },
    },
}


@dataclass(frozen=True)
class Study:
    title: str
    authors: str
    journal: str
    year: Optional[int]
    study_type: str
    abstract: str
    url: str
    pmid: Optional[str]
    open_access: bool
    cited_by: int


def _phrase(text: str) -> str:
    """Drop the characters that could end a quoted phrase early or escape out of it."""
    return re.sub(r'["\\]', "", text).strip()


def build_query(ingredient: str, concern: Optional[str], clinical_only: bool) -> str:
    """Europe PMC query: ingredient (and concern) in title/abstract, PubMed records only."""
    ingredient = _phrase(ingredient)
    if not ingredient:
        raise ValueError("ingredient is empty")
    parts = [f'TITLE_ABS:"{ingredient}"']
    concern = _phrase(concern or "")
    if concern:
        parts.append(f'TITLE_ABS:"{concern}"')
    parts.append("SRC:MED")
    if clinical_only:
        types = " OR ".join(f'PUB_TYPE:"{t}"' for t in CLINICAL_TYPES)
        parts.append(f"({types})")
    return " AND ".join(parts)


def strongest_study_type(pub_types: List[str]) -> str:
    lowered = [t.lower() for t in pub_types]
    for study_type in STUDY_TYPE_RANKING:
        if study_type in lowered:
            return study_type
    return "other"


def clean_abstract(text: str, max_chars: int = MAX_ABSTRACT_CHARS) -> str:
    """Drop the HTML tags Europe PMC leaves in abstracts and trim the length."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0] + " ..."
    return text


def parse_result(record: dict) -> Study:
    pub_types = record.get("pubTypeList", {}).get("pubType", [])
    if isinstance(pub_types, str):
        pub_types = [pub_types]
    pmid = record.get("pmid")
    year = record.get("pubYear")
    return Study(
        title=record.get("title", "").strip(),
        authors=record.get("authorString", ""),
        journal=record.get("journalInfo", {}).get("journal", {}).get("title", ""),
        year=int(year) if year and str(year).isdigit() else None,
        study_type=strongest_study_type(pub_types),
        abstract=clean_abstract(record.get("abstractText", "")),
        url=(
            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            if pmid
            else f"https://europepmc.org/article/{record.get('source')}/{record.get('id')}"
        ),
        pmid=pmid,
        open_access=record.get("isOpenAccess") == "Y",
        cited_by=int(record.get("citedByCount", 0) or 0),
    )


def search_studies(
    ingredient: str,
    concern: Optional[str] = None,
    limit: int = 5,
    clinical_only: bool = True,
    client: Optional[httpx.Client] = None,
) -> List[Study]:
    """Return up to `limit` studies, most relevant first."""
    params = {
        "query": build_query(ingredient, concern, clinical_only),
        "format": "json",
        "resultType": "core",
        "pageSize": limit,
    }
    try:
        if client is None:
            with httpx.Client(timeout=10) as own_client:
                response = own_client.get(EUROPE_PMC_SEARCH_URL, params=params)
        else:
            response = client.get(EUROPE_PMC_SEARCH_URL, params=params)
        response.raise_for_status()
        results = response.json().get("resultList", {}).get("result", [])
    except (httpx.HTTPError, ValueError) as error:  # ValueError: a non-JSON reply
        raise StudySearchError(
            "Europe PMC (the study database) is temporarily unavailable. "
            "Try again in a minute."
        ) from error
    return [parse_result(r) for r in results[:limit]]


def as_tool_result(studies: List[Study]) -> str:
    """The compact JSON string the model will receive as the tool result."""
    return json.dumps([asdict(s) for s in studies], ensure_ascii=False)


if __name__ == "__main__":
    # Try it: uv run python -m src.tools.studies niacinamide acne
    ingredient = sys.argv[1] if len(sys.argv) > 1 else "niacinamide"
    concern = sys.argv[2] if len(sys.argv) > 2 else None
    for study in search_studies(ingredient, concern):
        print(f"[{study.study_type}] {study.title} ({study.year})")
        print(f"  {study.journal} | cited by {study.cited_by} | {study.url}\n")
