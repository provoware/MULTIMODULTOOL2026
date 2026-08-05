from __future__ import annotations

from email.message import Message
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from urllib.error import HTTPError
from urllib.request import Request

from tools import collect_p3_009_main_signature_evidence as evidence


class _BytesResponse(io.BytesIO):
    status = 200

    def __enter__(self) -> "_BytesResponse":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class _RedirectOpener:
    def __init__(self, location: str) -> None:
        self.location = location
        self.request: Request | None = None

    def open(self, request: Request, timeout: int) -> _BytesResponse:
        self.request = request
        headers = Message()
        headers["Location"] = self.location
        raise HTTPError(request.full_url, 302, "Found", headers, None)


class ArtifactRedirectTests(unittest.TestCase):
    def test_download_keeps_token_at_github_api_boundary(self) -> None:
        api_url = "https://api.github.com/repos/provoware/MULTIMODULTOOL2026/actions/artifacts/7/zip"
        storage_url = "https://artifact-storage.example/signed.zip?signature=abc"
        opener = _RedirectOpener(storage_url)
        storage_requests: list[Request] = []

        def fake_urlopen(request: Request, timeout: int) -> _BytesResponse:
            storage_requests.append(request)
            return _BytesResponse(b"signed archive")

        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "artifact.zip"
            with (
                mock.patch.object(evidence, "build_opener", return_value=opener),
                mock.patch.object(evidence, "urlopen", side_effect=fake_urlopen),
            ):
                evidence._download(api_url, "secret-token", target)

            self.assertEqual(target.read_bytes(), b"signed archive")

        self.assertIsNotNone(opener.request)
        assert opener.request is not None
        self.assertEqual(opener.request.get_header("Authorization"), "Bearer secret-token")
        self.assertEqual(len(storage_requests), 1)
        self.assertEqual(storage_requests[0].full_url, storage_url)
        self.assertIsNone(storage_requests[0].get_header("Authorization"))

    def test_non_https_or_credentialed_redirect_is_blocked(self) -> None:
        unsafe_targets = (
            "http://artifact-storage.example/archive.zip",
            "https://user:password@artifact-storage.example/archive.zip",
        )
        for target in unsafe_targets:
            with self.subTest(target=target):
                opener = _RedirectOpener(target)
                with mock.patch.object(evidence, "build_opener", return_value=opener):
                    with self.assertRaises(evidence.EvidenceError):
                        evidence._redirect_target("https://api.github.com/artifact", "token")

    def test_oversized_partial_download_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "artifact.zip"
            with (
                mock.patch.object(evidence, "MAX_ARCHIVE_BYTES", 2),
                mock.patch.object(evidence, "urlopen", return_value=_BytesResponse(b"abc")),
            ):
                with self.assertRaises(evidence.EvidenceError):
                    evidence._stream_download("https://artifact-storage.example/archive.zip", target)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
