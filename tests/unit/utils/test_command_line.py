from slither.utils.command_line import check_and_sanitize_markdown_root


def test_bare_github_url_appends_blob_head():
    """Bare repo URL should append blob/HEAD/ for file linking."""
    result = check_and_sanitize_markdown_root("https://github.com/ORG/REPO/")
    assert result == "https://github.com/ORG/REPO/blob/HEAD/"


def test_bare_github_url_without_trailing_slash():
    """Missing trailing slash should be added, then blob/HEAD/ appended."""
    result = check_and_sanitize_markdown_root("https://github.com/ORG/REPO")
    assert result == "https://github.com/ORG/REPO/blob/HEAD/"


def test_tree_url_replaced_with_blob_head():
    """tree/ should be replaced with blob/HEAD for dynamic default branch."""
    result = check_and_sanitize_markdown_root("https://github.com/ORG/REPO/tree/main")
    assert result == "https://github.com/ORG/REPO/blob/HEAD/main/"


def test_blob_url_unchanged():
    """Already correct blob URLs should not be modified."""
    url = "https://github.com/ORG/REPO/blob/main/"
    result = check_and_sanitize_markdown_root(url)
    assert result == url


def test_non_github_url_unchanged():
    """Non-GitHub URLs should pass through unchanged."""
    url = "https://gitlab.com/ORG/REPO/"
    result = check_and_sanitize_markdown_root(url)
    assert result == url


def test_github_url_with_commit_sha():
    """URLs with commit SHA should not be modified (except trailing slash)."""
    result = check_and_sanitize_markdown_root(
        "https://github.com/ORG/REPO/blob/abc123def"
    )
    assert result == "https://github.com/ORG/REPO/blob/abc123def/"
