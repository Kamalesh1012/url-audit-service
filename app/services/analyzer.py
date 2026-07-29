"""Parses a fetched page and produces the SEO-facing fields: title,
meta description, canonical, robots, Open Graph tags, plus a scored
list of warnings/errors that explain the score."""
from bs4 import BeautifulSoup

from app.models.response import OpenGraphTags

TITLE_MIN, TITLE_MAX = 30, 60
META_DESC_MIN, META_DESC_MAX = 50, 160


class AnalysisError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class AnalysisResult:
    def __init__(self, title, meta_description, h1_count, canonical_url,
                 robots_tag, og_tags, errors, warnings, seo_score):
        self.title = title
        self.meta_description = meta_description
        self.h1_count = h1_count
        self.canonical_url = canonical_url
        self.robots_tag = robots_tag
        self.og_tags = og_tags
        self.errors = errors
        self.warnings = warnings
        self.seo_score = seo_score


def _og_content(soup: BeautifulSoup, prop: str) -> str | None:
    tag = soup.find("meta", attrs={"property": f"og:{prop}"})
    return tag.get("content", "").strip() if tag and tag.get("content") else None


def analyze(html: str, status_code: int) -> AnalysisResult:
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception as exc:  # pragma: no cover - BeautifulSoup is very forgiving
        raise AnalysisError(422, "unparseable_html", f"Could not parse response body: {exc}")

    errors: list[str] = []
    warnings: list[str] = []
    score = 100

    # --- HTTP status ---
    if status_code >= 500:
        errors.append(f"Page returned server error status {status_code}")
        score -= 30
    elif status_code >= 400:
        errors.append(f"Page returned client error status {status_code}")
        score -= 25
    elif status_code >= 300:
        warnings.append(f"Page returned redirect status {status_code}")
        score -= 5

    # --- Title ---
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None
    if not title:
        errors.append("Missing <title> tag")
        score -= 15
    elif not (TITLE_MIN <= len(title) <= TITLE_MAX):
        warnings.append(f"Title length ({len(title)} chars) is outside the recommended {TITLE_MIN}-{TITLE_MAX} range")
        score -= 5

    # --- Meta description ---
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag and meta_desc_tag.get("content") else None
    if not meta_description:
        warnings.append("Missing meta description")
        score -= 10
    elif not (META_DESC_MIN <= len(meta_description) <= META_DESC_MAX):
        warnings.append(
            f"Meta description length ({len(meta_description)} chars) is outside the recommended "
            f"{META_DESC_MIN}-{META_DESC_MAX} range"
        )
        score -= 5

    # --- H1 ---
    h1_tags = soup.find_all("h1")
    h1_count = len(h1_tags)
    if h1_count == 0:
        warnings.append("No <h1> tag found")
        score -= 10
    elif h1_count > 1:
        warnings.append(f"Multiple <h1> tags found ({h1_count}) — expected exactly 1")
        score -= 5

    # --- Canonical ---
    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    canonical_url = canonical_tag.get("href", "").strip() if canonical_tag and canonical_tag.get("href") else None
    if not canonical_url:
        warnings.append("Missing canonical link tag")
        score -= 5

    # --- Robots ---
    robots_tag_el = soup.find("meta", attrs={"name": "robots"})
    robots_tag = robots_tag_el.get("content", "").strip() if robots_tag_el and robots_tag_el.get("content") else None
    if robots_tag and ("noindex" in robots_tag.lower()):
        warnings.append("Page is set to 'noindex' — it will not appear in search results")
        score -= 10

    # --- Open Graph ---
    og_tags = OpenGraphTags(
        title=_og_content(soup, "title"),
        description=_og_content(soup, "description"),
        image=_og_content(soup, "image"),
        type=_og_content(soup, "type"),
        url=_og_content(soup, "url"),
    )
    if not og_tags.title and not og_tags.description and not og_tags.image:
        warnings.append("No Open Graph tags found — links will render poorly when shared")
        score -= 5

    score = max(0, min(100, score))

    return AnalysisResult(
        title=title,
        meta_description=meta_description,
        h1_count=h1_count,
        canonical_url=canonical_url,
        robots_tag=robots_tag,
        og_tags=og_tags,
        errors=errors,
        warnings=warnings,
        seo_score=score,
    )
