"""Score raw reply text and write a de-identified feature file.

Raw tweets are NOT distributed (X/Twitter terms allow sharing tweet IDs, not text), and user handles
are dropped. Run this locally against your own copy of the raw files:
    python scripts/score_replies.py raw/biden_replies.csv raw/trump_replies.csv
It writes data/reply_scores.csv with only numeric features and the account replied to."""
import re, sys
import numpy as np
import pandas as pd
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

VADER = SentimentIntensityAnalyzer()


def clean(t: str) -> str:
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"@\w+", " ", t)
    return re.sub(r"\s+", " ", t.replace("&amp;", "&")).strip()


def features(text: str) -> dict:
    c = clean(text); tb = TextBlob(c).sentiment; v = VADER.polarity_scores(c)
    words = re.findall(r"[A-Za-z']+", c)
    return {"n_words": len(words), "has_url": int(bool(re.search(r"https?://", text))), "n_mentions": len(re.findall(r"@\w+", text)),
            "n_hashtags": len(re.findall(r"#\w+", text)), "caps_share": np.mean([w.isupper() and len(w) > 1 for w in words]) if words else 0.0,
            "n_exclaim": text.count("!"), "has_question": int("?" in text), "textblob_polarity": tb.polarity,
            "textblob_subjectivity": tb.subjectivity, "vader_compound": v["compound"], "vader_pos": v["pos"], "vader_neg": v["neg"], "vader_neu": v["neu"]}


if __name__ == "__main__":
    out = []
    for path, account in zip(sys.argv[1:3], ["@JoeBiden", "@realDonaldTrump"]):
        raw = pd.read_csv(path)
        f = pd.DataFrame([features(t) for t in raw["text"].astype(str)])
        f.insert(0, "replied_to", account)
        out.append(f)
    res = pd.concat(out, ignore_index=True).sample(frac=1, random_state=0).reset_index(drop=True)  # shuffle: no ordering back to the source
    res.insert(0, "reply_id", range(1, len(res) + 1))
    res.round(4).to_csv("data/reply_scores.csv", index=False)
    print(res.shape)
