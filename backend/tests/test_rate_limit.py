_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def test_rate_limit_key_cannot_be_rotated(client, sample_docx):
    payload = sample_docx.read()
    codes = [
        client.post(
            "/api/compress/docx",
            files=[("file", ("t.docx", payload, _DOCX_MIME))],
            headers={"X-Forwarded-For": f"203.0.113.{i + 1}"},
        ).status_code
        for i in range(35)
    ]
    assert 429 in codes, "rotating X-Forwarded-For must not evade the limit"


def test_proxy_header_is_honoured_only_when_trusted(client, sample_docx, monkeypatch):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "true")
    payload = sample_docx.read()
    codes = [
        client.post(
            "/api/compress/docx",
            files=[("file", ("t.docx", payload, _DOCX_MIME))],
            headers={"X-Forwarded-For": f"198.51.100.{i + 1}"},
        ).status_code
        for i in range(35)
    ]
    assert 429 not in codes, "trusted proxies must still be able to forward client identity"
