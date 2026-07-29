from app.services.analyzer import analyze

GOOD_HTML = """
<html>
  <head>
    <title>A Well Optimized Page Title Here</title>
    <meta name="description" content="A meta description that sits comfortably inside the recommended length window for search engines.">
    <link rel="canonical" href="https://example.com/">
    <meta name="robots" content="index, follow">
    <meta property="og:title" content="A Well Optimized Page">
    <meta property="og:description" content="Great page">
    <meta property="og:image" content="https://example.com/img.png">
  </head>
  <body>
    <h1>Main Heading</h1>
    <p>Body content.</p>
  </body>
</html>
"""

BARE_HTML = "<html><body><p>nothing here</p></body></html>"


def test_analyze_good_page_scores_high():
    result = analyze(GOOD_HTML, 200)
    assert result.seo_score >= 90
    assert result.errors == []
    assert result.h1_count == 1
    assert result.canonical_url == "https://example.com/"
    assert result.robots_tag == "index, follow"
    assert result.og_tags.title == "A Well Optimized Page"


def test_analyze_bare_page_flags_everything_missing():
    result = analyze(BARE_HTML, 200)
    assert result.title is None
    assert result.meta_description is None
    assert result.canonical_url is None
    assert result.h1_count == 0
    assert any("title" in w.lower() for w in result.errors)
    assert any("h1" in w.lower() for w in result.warnings)
    assert any("canonical" in w.lower() for w in result.warnings)
    assert any("open graph" in w.lower() for w in result.warnings)
    assert result.seo_score < 70


def test_analyze_noindex_robots_flagged_as_warning():
    html = GOOD_HTML.replace('content="index, follow"', 'content="noindex"')
    result = analyze(html, 200)
    assert any("noindex" in w.lower() for w in result.warnings)


def test_analyze_multiple_h1_flagged():
    html = GOOD_HTML.replace("<h1>Main Heading</h1>", "<h1>One</h1><h1>Two</h1>")
    result = analyze(html, 200)
    assert result.h1_count == 2
    assert any("multiple" in w.lower() for w in result.warnings)


def test_analyze_server_error_status_adds_error_and_penalty():
    result = analyze(GOOD_HTML, 500)
    assert any("500" in e for e in result.errors)
    assert result.seo_score <= 70


def test_seo_score_never_negative():
    result = analyze(BARE_HTML, 500)
    assert 0 <= result.seo_score <= 100
