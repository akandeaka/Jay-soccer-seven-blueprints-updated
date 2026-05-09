# 📊 Akpel SOCCER BLUEPRINTS SYSTEM - TECHNICAL REPORT

## From Day 1 (May 6, 2026) to Present

---

## 🎯 SYSTEM OVERVIEW

The **Jay Soccer Blueprints System** is an automated soccer betting prediction engine that analyzes match odds using 8 predefined blueprints, applies AI validation, builds accumulators, and delivers predictions via Telegram with automatic performance validation.

---

## 📋 SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA INPUT LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  input_matches.txt (Manual copy/paste from Soccer24)            │
│  Format: Team A vs Team B | League | Home | Draw | Away Odds    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      BLUEPRINT ENGINE LAYER                      │
├─────────────────────────────────────────────────────────────────┤
│  BP1: Elite Home Banker (Home 1.20-1.29, Away ≥10.0)            │
│  BP2: Primary Favorite (Home 1.30-1.36, Away ≥9.0)              │
│  BP3: Moderate Favorite Safety (Home 1.30-1.36, Away 7.0-8.99)  │
│  BP4: Goal Engine (Home 1.72-1.80)                              │
│  BP5: Defensive Trap (Home 1.90-2.02)                           │
│  BP6: Strong Draw (Draw 2.75-3.39) → Full Time Draw (X)         │
│  BP7: BTTS Value Spot (Home 1.40-1.69 + League analysis)        │
│  BP8: High-Scoring Signals (Draw 3.60-3.75 + High-scoring league)│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         AI ANALYSIS LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  Confidence scoring (50-95%)                                    │
│  Decision types: VALIDATED (75%+), CONFIRMED (60-74%),          │
│                  ALTERNATIVE (<60%)                              │
│  League-based trend analysis for BP7/BP8                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      ACCUMULATOR BUILDER                         │
├─────────────────────────────────────────────────────────────────┤
│  2_ODDS: 2-3 matches @ 1.8-2.5 odds                             │
│  4_ODDS: 4 matches @ 3.5-5.0 odds                               │
│  7_ODDS: 5 matches @ 6.0-8.5 odds                               │
│  10_ODDS: 5-6 matches @ 9.0-12.0 odds                           │
│  Feature: NO duplicate matches across accumulators              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        OUTPUT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  Telegram Bot: Sends predictions with formatted messages        │
│  predictions.json: Saves results for validation                  │
│  Console output: Real-time processing logs                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      VALIDATION LAYER (1 AM)                      │
├─────────────────────────────────────────────────────────────────┤
│  actual_results.csv: Manual input of real scores                 │
│  ResultsValidator: Compares predictions vs actual               │
│  Performance Report: Accuracy by blueprint & confidence         │
│  Telegram: Performance summary sent                              │
│  History tracking: 30-day performance stored                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔵 THE 8 BLUEPRINTS (FINAL VERSION)

| BP | Name | Trigger Odds | Play | Confidence | Risk |
|----|------|--------------|------|------------|------|
| **BP1** | Elite Home Banker | Home 1.20-1.29, Away ≥10.0 | Straight Home Win | 95% | Ultra-Low |
| **BP2** | Primary Favorite | Home 1.30-1.36, Away ≥9.0 | Home Win | 90% | Low |
| **BP3** | Moderate Favorite Safety | Home 1.30-1.36, Away 7.0-8.99 | 1X & Over 1.5 Goals | 85% | Low-Moderate |
| **BP4** | Goal Engine | Home 1.72-1.80 | Over 1.5 Goals | 75% | Moderate |
| **BP5** | Defensive Trap | Home 1.90-2.02 | 1X & Under 3.5 FT | 70% | Moderate |
| **BP6** | Strong Draw | Draw 2.75-3.39 | Full Time Draw (X) | 50% | High |
| **BP7** | BTTS Value Spot | Home 1.40-1.69 | BTTS Yes/No | 75%/65% | Low-Moderate |
| **BP8** | High-Scoring Signals | Draw 3.60-3.75 + high-scoring league | HT 0.5 / Over 2.5 | 60% | Moderate-High |

---

## 🏆 HIGH-SCORING LEAGUES (For BP7 & BP8)

| League | Country | Average Goals |
|--------|---------|---------------|
| Bundesliga | Germany | 3.2 |
| Eredivisie | Netherlands | 3.1 |
| Premier League | England | 2.8 |
| Serie A | Italy | 2.6 |
| Ligue 1 | France | 2.5 |
| La Liga | Spain | 2.5 |

---

## 📁 FILE STRUCTURE

```
Jay-soccer-seven-blueprints-updated/
│
├── main.py                          # Main prediction system
├── run_validation.py                # Validation runner (1 AM)
├── results_validator.py             # Validation logic & reporting
├── config.py                        # Configuration (optional)
├── requirements.txt                 # Dependencies
│
├── input_matches.txt                # INPUT: Match data from Soccer24
├── actual_results.csv               # INPUT: Actual scores after matches
├── predictions.json                 # OUTPUT: Saved predictions
├── performance_report.md            # OUTPUT: Validation report
├── prediction_history.json          # OUTPUT: Historical performance
│
└── .github/workflows/
    └── daily_predictions.yml        # GitHub Actions automation
```

---

## 🔄 SYSTEM WORKFLOW

### Day 1 - Prediction Phase (10 AM)

```
1. User copies matches from Soccer24 → input_matches.txt
2. GitHub Actions triggers at 10 AM
3. main.py reads input_matches.txt
4. Parses matches (supports both text and CSV/tab formats)
5. Applies 8 blueprints to each match
6. AI analyzes confidence and decides VALIDATED/CONFIRMED/ALTERNATIVE
7. Builds accumulators from predictions only (no duplicates across accumulators)
8. Sends formatted predictions to Telegram
9. Saves predictions to predictions.json
```

### Day 2 - Validation Phase (1 AM)

```
1. GitHub Actions triggers at 1 AM
2. run_validation.py loads predictions.json
3. User provides actual_results.csv with real scores
4. Validator compares predictions vs actual results
5. Calculates accuracy by blueprint and confidence level
6. Generates performance_report.md
7. Updates prediction_history.json (30-day rolling history)
8. Sends performance summary to Telegram
```

---

## 📊 ACCUMULATOR LOGIC

| Accumulator | Target Odds | Matches | Selection Method |
|-------------|-------------|---------|------------------|
| **2_ODDS** | 1.8 - 2.5 | 2-3 | Highest confidence picks |
| **4_ODDS** | 3.5 - 5.0 | 4 | Next available picks (no duplicates) |
| **7_ODDS** | 6.0 - 8.5 | 5 | Remaining picks |
| **10_ODDS** | 9.0 - 12.0 | 5-6 | Remaining picks |

**Key Feature:** Each accumulator uses **unique matches** - no match appears in more than one accumulator.

---

## 🤖 AI DECISION LOGIC

```python
if confidence >= 75:
    decision = "VALIDATED"      # Strong confidence, recommended bet
elif confidence >= 60:
    decision = "CONFIRMED"      # Good confidence, acceptable bet
else:
    decision = "ALTERNATIVE"    # Low confidence, consider alternative
```

---

## 📈 VALIDATION METRICS

| Metric | Calculation |
|--------|-------------|
| **Overall Accuracy** | (Correct Predictions / Total Predictions) × 100 |
| **Accuracy by Blueprint** | Per BP: (BP correct / BP total) × 100 |
| **Accuracy by Confidence** | High (75%+), Medium (60-74%), Low (<60%) |
| **ROI** | Correct picks - Wrong picks (assuming 1 unit per pick) |

---

## 🔧 TECHNICAL SPECIFICATIONS

| Component | Specification |
|-----------|---------------|
| **Language** | Python 3.11 |
| **Dependencies** | requests, pandas |
| **Input Format** | Text with "Team A vs Team B" + odds line with "|" |
| **Output Format** | HTML-formatted Telegram messages |
| **Schedule** | 10 AM (predictions), 1 AM (validation) |
| **Platform** | GitHub Actions (Ubuntu latest) |
| **Data Source** | Soccer24 (manual copy/paste) |

---

## 📝 INPUT FORMAT EXAMPLE

```text
Aston Villa vs Nottingham
Europa League
1.73 | 3.9 | 4.5

Crystal Palace vs Shakhtar Donetsk
Conference League
1.57 | 4.2 | 5.75
```

---

## 📤 OUTPUT EXAMPLE (Telegram)

```
⚽ JAY SOCCER BLUEPRINTS - AI PREDICTIONS
📅 2026-05-07 16:35
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 AI ANALYZED PICKS

✅ BP3: Pogradeci vs Kastrioti
   🎯 1X & Over 1.5 Goals
   📈 AI Confidence: 85%
   🔍 Decision: VALIDATED

🟡 BP7: Oran vs ASO Chlef
   🎯 Both Teams to Score - YES
   📈 AI Confidence: 75%
   🔍 Decision: VALIDATED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎰 ACCUMULATOR PICKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2_ODDS (Target: 2 odds)
Total Odds: 1.81
   1. Pogradeci vs Kastrioti
      🎯 1X & Over 1.5 Goals
   2. Oran vs ASO Chlef
      🎯 Both Teams to Score - YES
```

---

## ✅ KEY FEATURES ACHIEVED

| Feature | Status |
|---------|--------|
| Read Soccer24 copy/paste data | ✅ Complete |
| 8 Blueprints as defined | ✅ Complete |
| AI validation (VALIDATED/CONFIRMED/ALTERNATIVE) | ✅ Complete |
| Accumulators (2,4,7,10 odds) | ✅ Complete |
| No duplicate matches across accumulators | ✅ Complete |
| Telegram integration | ✅ Complete |
| GitHub Actions automation | ✅ Complete |
| Results validation (1 AM) | ✅ Complete |
| Performance reporting | ✅ Complete |
| 30-day history tracking | ✅ Complete |
| No demo data | ✅ Complete |
| BP6 as Full Time Draw (X) | ✅ Complete |

---

## 📊 PERFORMANCE REPORT EXAMPLE

```markdown
# 📊 SOCCER BLUEPRINT SYSTEM - PERFORMANCE REPORT

**Date:** 2026-05-08
**Total Predictions:** 15
**Matches Validated:** 15
**Correct Predictions:** 10
**Overall Accuracy:** 66.7%

## 📈 Accuracy by Blueprint

| Blueprint | Predictions | Correct | Accuracy |
|-----------|-------------|---------|----------|
| BP1 | 2 | 2 | 100.0% |
| BP3 | 3 | 3 | 100.0% |
| BP4 | 4 | 2 | 50.0% |
| BP7 | 6 | 3 | 50.0% |
```

---

## 🚀 DEPLOYMENT

### GitHub Secrets Required

| Secret | Purpose |
|--------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot authentication |
| `TELEGRAM_CHAT_ID` | Telegram chat destination |

### Manual Trigger

```bash
# Run predictions
python main.py

# Run validation (after entering actual scores)
python run_validation.py
```

### Automated Schedule

| Time | Action |
|------|--------|
| 10 AM UTC | Predictions generated |
| 1 AM UTC | Validation runs |

---

## 📅 DEVELOPMENT TIMELINE

| Date | Milestone |
|------|-----------|
| May 6, 2026 (Morning) | Initial system design, 8 blueprints defined |
| May 6, 2026 (Afternoon) | Data parser, blueprint engine, AI analysis |
| May 6, 2026 (Evening) | Telegram integration, accumulator builder |
| May 7, 2026 (Early) | CSV/Tab format support added |
| May 7, 2026 (Mid) | BP6 corrected to Full Time Draw (X) |
| May 7, 2026 (Late) | Accumulator duplicate fix, validation system |
| Present | Complete production-ready system |

---

## ✅ SYSTEM STATUS

| Component | Status | Notes |
|-----------|--------|-------|
| Data Input | ✅ Operational | Copy/paste from Soccer24 |
| Blueprint Filter | ✅ Operational | 8 blueprints active |
| AI Analysis | ✅ Operational | 3 decision types |
| Accumulators | ✅ Operational | 4 targets, no duplicates |
| Telegram Sending | ✅ Operational | HTML formatted |
| Validation | ✅ Operational | 1 AM daily |
| Performance Reports | ✅ Operational | Accuracy tracking |

---

**System is production-ready and fully operational.** 🚀
