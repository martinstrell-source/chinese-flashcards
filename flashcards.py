import json
import random
import re

with open("flashcards.json") as f:
    flashcards = json.load(f)

TONE_MARKS = {
    'a': 'āáǎàa',
    'e': 'ēéěèe',
    'i': 'īíǐìi',
    'o': 'ōóǒòo',
    'u': 'ūúǔùu',
    'v': 'ǖǘǚǜü',
}

def apply_tone(syllable, tone):
    if tone == 5:
        return syllable.replace('v', 'ü')
    idx = tone - 1
    for v in ['a', 'e']:
        if v in syllable:
            return syllable.replace(v, TONE_MARKS[v][idx])
    if 'ou' in syllable:
        return syllable.replace('o', TONE_MARKS['o'][idx], 1)
    for i in range(len(syllable) - 1, -1, -1):
        if syllable[i] in TONE_MARKS:
            return syllable[:i] + TONE_MARKS[syllable[i]][idx] + syllable[i+1:]
    return syllable.replace('v', 'ü')

def numbered_to_tone_marks(text):
    def replace_syllable(m):
        syllable = m.group(1).lower()
        tone = int(m.group(2)) if m.group(2) else 5
        return apply_tone(syllable, tone)
    return re.sub(r'([a-zA-Z]+)([1-5]?)', replace_syllable, text)

random.shuffle(flashcards)

print("Chinese Flashcards")
print("-------------------")
print("(Tip: type tone as a number after each syllable, e.g. ni3 or hao3)")

correct = 0
incorrect = 0

def run_cards(cards):
    global correct, incorrect
    wrong = []
    for card in cards:
        print(f"\nCharacter: {card['hanzi']}")
        guess = input("Your pinyin guess: ").strip()
        normalized = numbered_to_tone_marks(guess)

        if normalized.lower() == card['pinyin'].lower():
            print("Correct!")
            correct += 1
        else:
            print(f"Incorrect. Pinyin: {card['pinyin']}")
            incorrect += 1
            wrong.append(card)

        print(f"Meaning: {card['meaning']}")
        input("Press Enter for next card...")
    return wrong

wrong = run_cards(flashcards)

while wrong:
    print(f"\n-------------------")
    print(f"Retesting {len(wrong)} card(s) you got wrong...")
    random.shuffle(wrong)
    wrong = run_cards(wrong)

total = correct + incorrect
print("\n-------------------")
print(f"Results: {correct}/{total} correct ({incorrect} incorrect)")