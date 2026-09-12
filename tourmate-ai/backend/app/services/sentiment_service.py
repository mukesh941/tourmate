import re
from typing import Dict, Any, Optional

# Curated tourism domain sentiment lexicon with valence ratings (-4 to +4)
TOURISM_LEXICON: Dict[str, float] = {
    # Highly positive (+3 to +4)
    "breathtaking": 3.8,
    "stunning": 3.6,
    "magnificent": 3.7,
    "exceptional": 3.6,
    "phenomenal": 3.8,
    "spectacular": 3.6,
    "unforgettable": 3.5,
    "paradise": 3.5,
    "divine": 3.4,
    "magical": 3.5,
    "pristine": 3.3,
    "mesmerizing": 3.5,
    "flawless": 3.6,
    "outstanding": 3.5,
    "splendid": 3.4,
    "superb": 3.5,

    # Positive (+1.5 to +3)
    "beautiful": 2.8,
    "amazing": 2.9,
    "wonderful": 2.8,
    "excellent": 2.9,
    "clean": 2.4,
    "comfortable": 2.3,
    "peaceful": 2.4,
    "serene": 2.5,
    "hospitable": 2.6,
    "friendly": 2.2,
    "helpful": 2.0,
    "luxurious": 2.7,
    "delicious": 2.5,
    "scenic": 2.4,
    "enjoyed": 2.1,
    "loved": 2.8,
    "great": 2.0,
    "good": 1.5,
    "nice": 1.4,
    "pleasant": 1.8,
    "recommended": 2.3,
    "charming": 2.3,
    "historic": 1.5,
    "cozy": 2.0,
    "gem": 2.5,
    "safe": 2.0,
    "best": 2.7,
    "awesome": 2.6,
    "fantastic": 2.8,
    "worth": 1.8,

    # Mildly negative / negative (-1.5 to -2.8)
    "crowded": -1.8,
    "noisy": -1.9,
    "overpriced": -2.4,
    "expensive": -1.6,
    "slow": -1.5,
    "average": -0.5,
    "mediocre": -1.8,
    "boring": -2.0,
    "smelly": -2.3,
    "dirty": -2.6,
    "unclean": -2.5,
    "rude": -2.7,
    "uncomfortable": -2.4,
    "poor": -2.2,
    "delay": -1.7,
    "delayed": -1.7,
    "disappointing": -2.5,
    "disappointed": -2.6,
    "maintenance": -1.2,
    "lack": -1.4,
    "waste": -2.7,
    "avoid": -2.8,

    # Severely negative (-3 to -4)
    "horrible": -3.5,
    "terrible": -3.5,
    "awful": -3.6,
    "scam": -3.8,
    "fraud": -3.8,
    "worst": -3.7,
    "pathetic": -3.4,
    "disgusting": -3.6,
    "unsafe": -3.3,
    "nightmare": -3.7,
    "regret": -3.2,
}

NEGATION_WORDS = {
    "not", "no", "never", "neither", "nowhere", "hardly", "scarcely",
    "barely", "didnt", "didn't", "wasnt", "wasn't", "couldnt", "couldn't",
    "dont", "don't", "isnt", "isn't", "without"
}

BOOSTER_WORDS = {
    "very": 1.4,
    "extremely": 1.7,
    "absolutely": 1.6,
    "really": 1.3,
    "incredibly": 1.6,
    "super": 1.4,
    "highly": 1.4,
    "totally": 1.3,
    "quite": 1.2,
    "so": 1.3,
}

def analyze_sentiment(text: str, user_rating: Optional[int] = None) -> Dict[str, Any]:
    """
    Analyzes tourist review text using Natural Language Processing (NLP) heuristics,
    lexicon valence scoring, negation flipping, and rating calibration.
    Fulfills VTU Synopsis slide 10 & 15 requirement for Tourist Review Sentiment Analysis.
    """
    if not text or not text.strip():
        # Fallback to rating if available
        if user_rating is not None:
            if user_rating >= 4:
                return {
                    "sentiment_label": "Positive",
                    "sentiment_score": 0.85,
                    "sentiment_emoji": "😊",
                    "polarity": 0.5
                }
            elif user_rating == 3:
                return {
                    "sentiment_label": "Neutral",
                    "sentiment_score": 0.70,
                    "sentiment_emoji": "😐",
                    "polarity": 0.0
                }
            else:
                return {
                    "sentiment_label": "Negative",
                    "sentiment_score": 0.85,
                    "sentiment_emoji": "🙁",
                    "polarity": -0.5
                }
        return {
            "sentiment_label": "Neutral",
            "sentiment_score": 0.50,
            "sentiment_emoji": "😐",
            "polarity": 0.0
        }

    # Clean and tokenize words
    words = re.findall(r"\b[A-Za-z']+\b", text.lower())
    if not words:
        return {
            "sentiment_label": "Neutral",
            "sentiment_score": 0.50,
            "sentiment_emoji": "😐",
            "polarity": 0.0
        }

    score_sum = 0.0
    matched_count = 0

    for i, word in enumerate(words):
        val = TOURISM_LEXICON.get(word, None)
        if val is not None:
            # Check previous 2 tokens for negation or boosters
            multiplier = 1.0
            is_negated = False

            if i > 0:
                prev_1 = words[i - 1]
                if prev_1 in NEGATION_WORDS:
                    is_negated = True
                elif prev_1 in BOOSTER_WORDS:
                    multiplier = BOOSTER_WORDS[prev_1]

            if i > 1 and not is_negated:
                prev_2 = words[i - 2]
                if prev_2 in NEGATION_WORDS:
                    is_negated = True
                elif prev_2 in BOOSTER_WORDS and multiplier == 1.0:
                    multiplier = BOOSTER_WORDS[prev_2]

            if is_negated:
                val = -0.8 * val

            score_sum += (val * multiplier)
            matched_count += 1

    # Text polarity normalized between -1.0 and 1.0
    if matched_count > 0:
        raw_polarity = score_sum / (matched_count * 3.5)
        polarity = max(-1.0, min(1.0, raw_polarity))
    else:
        polarity = 0.0

    # Bayesian blending with star rating prior (if provided)
    if user_rating is not None:
        rating_polarity = (user_rating - 3) / 2.0  # 1 -> -1.0, 3 -> 0.0, 5 -> 1.0
        # 60% text evidence + 40% rating calibration
        polarity = 0.6 * polarity + 0.4 * rating_polarity

    # Classification into Positive, Neutral, Negative
    if polarity >= 0.15:
        label = "Positive"
        emoji = "😊"
        confidence = 0.65 + min(0.34, abs(polarity) * 0.35)
    elif polarity <= -0.15:
        label = "Negative"
        emoji = "🙁"
        confidence = 0.65 + min(0.34, abs(polarity) * 0.35)
    else:
        label = "Neutral"
        emoji = "😐"
        confidence = 0.70 + (0.15 - abs(polarity))

    return {
        "sentiment_label": label,
        "sentiment_score": round(confidence, 2),
        "sentiment_emoji": emoji,
        "polarity": round(polarity, 2)
    }
