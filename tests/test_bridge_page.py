import os
import pytest
from my_automated_traffic.bridge_page import QuizPageGenerator

def test_quiz_generation(tmp_path):
    generator = QuizPageGenerator(str(tmp_path))
    output_file = generator.generate(
        title="Dating Blueprint Quiz",
        offer_url="http://nsfw-offer.com",
        niche="dating"
    )
    assert os.path.exists(output_file)
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "Dating Blueprint Quiz" in content
        assert "http://nsfw-offer.com" in content
        assert 'data-url="http://nsfw-offer.com"' in content
        assert 'addEventListener' in content

def test_invalid_offer_url(tmp_path):
    generator = QuizPageGenerator(str(tmp_path))
    with pytest.raises(ValueError, match="Offer URL must start with http:// or https://"):
        generator.generate(
            title="Dating Quiz",
            offer_url="javascript:alert(1)",
            niche="dating"
        )

def test_path_traversal_and_invalid_niche(tmp_path):
    generator = QuizPageGenerator(str(tmp_path))
    with pytest.raises(ValueError):
        generator.generate(
            title="Dating Quiz",
            offer_url="http://nsfw-offer.com",
            niche="../../../etc/passwd"
        )
    with pytest.raises(ValueError):
        generator.generate(
            title="Dating Quiz",
            offer_url="http://nsfw-offer.com",
            niche=""
        )

def test_html_escaping(tmp_path):
    generator = QuizPageGenerator(str(tmp_path))
    output_file = generator.generate(
        title="<script>alert(1)</script> Dating Quiz",
        offer_url="http://nsfw-offer.com",
        niche="dating"
    )
    assert os.path.exists(output_file)
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "&lt;script&gt;alert(1)&lt;/script&gt; Dating Quiz" in content
        assert "<script>alert(1)</script>" not in content
