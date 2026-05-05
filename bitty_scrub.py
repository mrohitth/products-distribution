#!/usr/bin/env python3
"""
bitty_scrub.py — Strips AI-isms from Markdown files to give them a "Human-Only" feel.
Run with: python3 bitty_scrub.py <input.md> [output.md]

If no output path given, overwrites the input file in place.
"""

import re
import sys

# Patterns that scream "AI-written"
AIISMS = [
    (r"\bIn conclusion[,\s]", "Ultimately,"),
    (r"\bIn today's fast-paced world\b", "In this day and age,"),
    (r"\bIt's worth noting that\b", "Importantly,"),
    (r"\bAs aforementioned\b", "As noted,"),
    (r"\bTo summarize\b", "In short,"),
    (r"\bDelve\b", "Explore"),
    (r"\bDelving\b", "Exploring"),
    (r"\bCrucial\b", "Key"),
    (r"\bEssential\b", "Important"),
    (r"\bFacilitate\b", "Help"),
    (r"\bUtilize\b", "Use"),
    (r"\bImplement\b", "Do"),
    (r"\bLeverage\b", "Use"),
    (r"\bIn a world where\b", ""),
    (r"\bThe fact that\b", "That"),
    (r"\bGiven the fact that\b", "Since"),
    (r"\bOwing to the fact that\b", "Since"),
    (r"\bFor the purpose of\b", "To"),
    (r"\bIn order to\b", "To"),
    (r"\bWith regard to\b", "About"),
    (r"\bIn reference to\b", "About"),
    (r"\bAt the end of the day\b", "Ultimately,"),
    (r"\bNeedless to say\b", ""),
    (r"\bIt goes without saying\b", ""),
    (r"\bAs you can see\b", ""),
    (r"\bAs we all know\b", ""),
    (r"\bIt is important to note\b", "Note:"),
    (r"\bOne of the most important\b", "A key"),
    (r"\bFirst and foremost\b", "First,"),
    (r"\bLast but not least\b", "Finally,"),
    (r"\bAll things considered\b", "Overall,"),
    (r"\bTaking everything into account\b", "Overall,"),
    (r"\bThe question remains\b", ""),
    (r"\bThis raises the question\b", ""),
    (r"\bIt is clear that\b", ""),
    (r"\bIt is evident that\b", ""),
    (r"\bOne can conclude that\b", ""),
    (r"\bIn summary\b", "Overall,"),
    (r"\bTo conclude\b", "In closing,"),
    (r"\bIn closing\b", "Finally,"),
    (r"\bWhen all is said and done\b", "Ultimately,"),
    (r"\bAt the end of the day\b", "Ultimately,"),
    (r"\bDon't forget to\b", "Remember to"),
    (r"\bMake sure to\b", "Remember to"),
    (r"\bIt is recommended that\b", ""),
    (r"\bIt is advised\b", ""),
    (r"\bYou may want to consider\b", "Consider"),
    (r"\bIt is beneficial to\b", "It helps to"),
    (r"\bProvides? a comprehensive\b", "Gives a full"),
    (r"\bOffers? a unique\b", "Gives a"),
    (r"\bCutting-edge\b", "Advanced"),
    (r"\bState-of-the-art\b", "Advanced"),
    (r"\bGame-changing\b", "Useful"),
    (r"\bRevolutionize[sd]?\b", "Changed"),
    (r"\bTransform[ed]?\b", "Changed"),
    (r"\bUnlock[s]?\b", "Opens"),
    (r"\bUnleash[es]?\b", "Brings"),
    (r"\bDive[s]? into\b", "Explore[s]?"),
    (r"\bEmbark on\b", "Start"),
    (r"\bJourney through\b", "Explore"),
    (r"\bMaster the art of\b", "Learn to"),
    (r"\bDiscover the secrets?\b", "Learn"),
    (r"\bSecret[s]?\s+(?:of|to|for)\b", "Key"),
    (r"\bHere's the thing\b", "The reality is"),
    (r"\bLet's face it\b", "The truth is"),
    (r"\bBottom line\b", "The key point"),
    (r"\bThe thing is\b", ""),
    (r"\bTrust me\b", ""),
    (r"\bBelieve me\b", ""),
    (r"\bSimply put\b", ""),
    (r"\bIn simple terms\b", ""),
    (r"\bPlainly stated\b", ""),
    (r"\bTo put it simply\b", ""),
    (r"\bSo, what does this mean for you\?\b", "What this means for you:"),
    (r"\bThis means\b", "This"),
    (r"\bWhich brings us to\b", "Now we come to"),
    (r"\bNow, you might be wondering\b", "You might wonder"),
    (r"\bYou might be asking yourself\b", "You may wonder"),
    # Filler phrases
    (r"\bAnywho[,\s]", ""),
    (r"\bSo without further ado\b", ""),
    (r"\bWithout further ado\b", "Now"),
    (r"\bWelp\b", "Well"),
]

# Sections that should be flagged for human review
REVIEW_FLAGS = [
    (r"\b\[TODO\]", "[TODO — HUMAN REVIEW REQUIRED]"),
    (r"\b\[HUMAN\??\]", "[NEEDS HUMAN TOUCH]"),
]

def scrub_file(input_path: str, output_path: str = None) -> int:
    """Scrub AI-isms from a markdown file. Returns count of replacements made."""
    if output_path is None:
        output_path = input_path  # overwrite in place

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    replacements = 0
    for pattern, replacement in AIISMS:
        new_content, count = re.subn(pattern, replacement, content, flags=re.IGNORECASE)
        if count > 0:
            replacements += count
            content = new_content

    # Flag TODO sections
    for pattern, flag in REVIEW_FLAGS:
        content, count = re.subn(pattern, flag, content, flags=re.IGNORECASE)
        replacements += count

    # Clean up double spaces from removed phrases
    content = re.sub(r"  +", " ", content)
    # Clean up orphaned punctuation
    content = re.sub(r"\b, ([,.])", r"\1", content)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return replacements

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 bitty_scrub.py <input.md> [output.md]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        count = scrub_file(input_file, output_file)
        out = output_file or input_file
        print(f"bitty_scrub: {count} AI-isms stripped from {out}")
    except FileNotFoundError:
        print(f"ERROR: File not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
