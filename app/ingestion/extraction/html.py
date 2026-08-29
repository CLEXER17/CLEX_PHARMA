from selectolax.parser import HTMLParser


def extract_html(html: str) -> dict[str, str]:
    tree = HTMLParser(html)
    for node in tree.css("script, style, noscript"):
        node.decompose()
    title = tree.css_first("h1") or tree.css_first("title")
    text = " ".join(tree.body.text(separator=" ").split()) if tree.body else ""
    return {
        "title": title.text(strip=True) if title else "Not specified / Not verified",
        "text": text[:100_000],
    }
