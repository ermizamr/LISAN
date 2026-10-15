# LISAN Test Suite

This directory contains automated integration, scenario, and linguistic repair tests for the LISAN platform.

## Test Categories

* **Pipeline & Auto-Routing:**
  * `test_pipeline_real.py`: Tests end-to-end translation using real recorded audio inputs across Amharic, Oromo, Tigrinya, and English.
  * `test_auto_routing.py`: Tests bidirectional audio language detection.
  * `test_smart_pipeline.py`: Tests hybrid routing between Translation Memory and NLLB.
  * `test_speech_repairs.py`: Tests regex and morphological repairs for Ethiopian languages.

* **Domain Scenarios:**
  * `test_scenario_clinic.py`: Clinic triage and medical consultation dialogue tests.
  * `test_scenario_banking.py`: Financial and bank teller interaction scenarios.
  * `test_scenario_market.py`: Market and bazaar trade negotiation scenarios.
  * `test_scenario_police.py`: Emergency and police check-post scenarios.
  * `test_scenario_road.py`: Rural transit and travel directions scenarios.
  * `test_scenario_cafe.py`: Hospitality and dining interaction scenarios.
  * `test_scenario_school.py`: Academic and community education scenarios.
  * `test_scenario_kebele.py`: Kebele / municipal administrative dialogue scenarios.

* **Speech Synthesis & Recognition:**
  * `test_tts_amharic.py` / `test_tts_tigrinya.py`: On-device VITS phoneme-to-audio synthesis tests.
  * `test_oromo_end_to_end.py`: End-to-end Afaan Oromoo STT $\to$ NMT $\to$ VITS test.
  * `test_zero_fail.py`: Zero-fail resilience regression suite for mobile fallbacks.

## Running Tests

From the project root:

```bash
# Run pytest across all test suites
pytest tests/

# Run a specific test
python tests/test_speech_repairs.py
```
