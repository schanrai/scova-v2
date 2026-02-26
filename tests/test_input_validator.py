"""Tests for input_validator.py. Port of __tests__/lib/input-validator.test.ts."""

import pytest

from py_app.validators.input_validator import (
    detect_sql_injection,
    detect_xss,
    detect_template_injection,
    detect_prompt_injection,
    detect_json_injection,
    detect_repeated_characters,
    detect_gibberish,
    detect_invalid_length,
    validate_company_name,
    validate_region_name,
    validate_division_name,
    validate_numeric_choice,
    is_input_safe,
    validate_prompt,
)


class TestSQLInjectionDetection:
    def test_detect_basic_sql_injection_patterns(self):
        assert detect_sql_injection("Company'; DROP TABLE users--") is True
        assert detect_sql_injection("OR 1=1") is True
        assert detect_sql_injection("or 1=1") is True
        assert detect_sql_injection("UNION SELECT * FROM users") is True
        assert detect_sql_injection("'; DELETE FROM users--") is True
        assert detect_sql_injection("drop table users") is True
        assert detect_sql_injection("SELECT * FROM users") is True

    def test_allow_valid_company_names_sql(self):
        assert detect_sql_injection("Apple Inc") is False
        assert detect_sql_injection("Microsoft Corporation") is False
        assert detect_sql_injection("Johnson & Johnson") is False


class TestXSSDetection:
    def test_detect_xss_script_tags(self):
        assert detect_xss("<script>alert('test')</script>") is True
        assert detect_xss('<img onerror="alert(1)">') is True
        assert detect_xss("javascript:alert(1)") is True
        assert detect_xss('<iframe src="evil.com"></iframe>') is True

    def test_allow_valid_company_names_xss(self):
        assert detect_xss("Apple Inc") is False
        assert detect_xss("Microsoft Corporation") is False


class TestTemplateInjectionDetection:
    def test_detect_template_injection_patterns(self):
        assert detect_template_injection("${process.env.API_KEY}") is True
        assert detect_template_injection("{{malicious}}") is True
        assert detect_template_injection("<% code %>") is True

    def test_allow_valid_company_names_template(self):
        assert detect_template_injection("Apple Inc") is False


class TestJSONInjectionDetection:
    def test_detect_json_like_input(self):
        assert detect_json_injection('{"TEST": "VALUE"}') is True
        assert detect_json_injection('["test", "value"]') is True
        assert detect_json_injection('{"test": "value"}') is True

    def test_allow_valid_company_names_json(self):
        assert detect_json_injection("Apple Inc") is False


class TestPatternDetection:
    def test_detect_repeated_characters(self):
        assert detect_repeated_characters("aaaaa") is True
        assert detect_repeated_characters("Apple") is False

    def test_detect_invalid_length(self):
        assert detect_invalid_length("") is True
        assert detect_invalid_length("a") is True
        assert detect_invalid_length("ab") is False
        assert detect_invalid_length("Apple") is False


class TestCompanyNameValidation:
    def test_validate_legitimate_company_names(self):
        r1 = validate_company_name("Apple Inc")
        assert r1.is_valid is True
        assert r1.blocked is False

        r2 = validate_company_name("Microsoft Corporation")
        assert r2.is_valid is True
        assert r2.blocked is False

        r3 = validate_company_name("Johnson & Johnson")
        assert r3.is_valid is True

    def test_block_sql_injection_attempts(self):
        r = validate_company_name("Company'; DROP TABLE--")
        assert r.is_valid is False
        assert r.blocked is True

    def test_block_xss_attempts(self):
        r = validate_company_name("<script>alert('test')</script>")
        assert r.is_valid is False
        assert r.blocked is True

    def test_block_template_injection_attempts(self):
        r = validate_company_name("${process.env.API_KEY}")
        assert r.is_valid is False
        assert r.blocked is True

    def test_block_json_injection_attempts(self):
        r = validate_company_name('{"TEST": "VALUE"}')
        assert r.is_valid is False
        assert r.blocked is True

    def test_block_repeated_characters(self):
        r = validate_company_name("aaaaaaaaaaa")
        assert r.is_valid is False
        assert r.blocked is True

    def test_reject_empty_input(self):
        r = validate_company_name("")
        assert r.is_valid is False
        assert r.blocked is False

    def test_reject_too_short_input(self):
        r = validate_company_name("a")
        assert r.is_valid is False
        assert r.blocked is True


class TestIsInputSafe:
    def test_return_true_for_safe_input(self):
        assert is_input_safe("Apple Inc") is True
        assert is_input_safe("Microsoft Corporation") is True

    def test_return_false_for_unsafe_input(self):
        assert is_input_safe("Company'; DROP TABLE--") is False
        assert is_input_safe("<script>alert('test')</script>") is False
        assert is_input_safe("${process.env.API_KEY}") is False
        assert is_input_safe('{"TEST": "VALUE"}') is False
        assert is_input_safe("aaaaaaaaaaa") is False


class TestPromptValidation:
    def test_validate_safe_prompts(self):
        r = validate_prompt("Research company Apple Inc")
        assert r.is_valid is True
        assert r.blocked is False

    def test_block_prompts_with_sql_injection(self):
        r = validate_prompt("Company'; DROP TABLE--")
        assert r.is_valid is False
        assert r.blocked is True

    def test_block_prompts_with_xss(self):
        r = validate_prompt("<script>alert('test')</script>")
        assert r.is_valid is False
        assert r.blocked is True


class TestNumericChoiceValidation:
    def test_validate_correct_numeric_choices(self):
        r = validate_numeric_choice("1", ["1", "2", "3"])
        assert r.is_valid is True

    def test_reject_invalid_numeric_choices(self):
        r = validate_numeric_choice("4", ["1", "2", "3"])
        assert r.is_valid is False
