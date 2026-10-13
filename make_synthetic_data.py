"""Generate the synthetic chief-problem table used by analysis.ipynb.

Every value is drawn with a seeded random number generator from the phrase bank and
profiles below. Nothing is read from any external file.

Output: synthetic/synthetic_chief_problems.csv (one row per chief-problem sentence)
        synthetic/codebook.csv (105 items, 20 domains)
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261004
OUT = Path(__file__).resolve().parent / "synthetic"

# ---------------------------------------------------------------- codebook
ITEMS = {
    1: "Delusion", 2: "Hallucination", 3: "Disorganized speech", 4: "Disorganized behavior",
    5: "Negative symptom", 6: "Stupor", 7: "Catalepsy", 8: "Mutism", 9: "Posturing",
    10: "Inflated self-esteem or grandiosity", 11: "Elevated, expansive, or irritable mood",
    12: "Increased goal-directed activity or energy", 13: "Decreased need for sleep",
    14: "More talkative", 15: "Flight of ideas / thought racing", 16: "Distractibility",
    17: "Excessive involvement in high-risk activities", 18: "Obsession", 19: "Compulsion",
    20: "Depressed mood", 21: "Markedly diminished interest or pleasure",
    22: "Significant weight/appetite change", 23: "Psychomotor agitation or retardation",
    24: "Fatigue or loss of energy",
    25: "Feeling of worthlessness or excessive/inappropriate guilt",
    26: "Diminished ability to think or concentrate, or indecisiveness",
    27: "Low self-esteem", 28: "Feeling of hopelessness",
    29: "Marked fear about specific object/situation",
    30: "Phobic object/situation actively avoided", 31: "Marked fear about social situation",
    32: "Palpitation, pounding heart, accelerated heart rate",
    33: "Shortness of breath or smothering", 34: "Feeling of choking",
    35: "Fear of losing control or going crazy", 36: "Fear of dying",
    37: "Persistent concern about additional panic attacks",
    38: "Significant maladaptive behavior change related to attacks",
    39: "Excessive anxiety and worry", 40: "Difficult to control the worry",
    41: "Severe recurrent temper outburst", 42: "Irritability",
    43: "Recurrent intrusive distressing memories of traumatic event",
    44: "Dissociative reactions (flashbacks)",
    45: "Avoidance of distressing memories/thoughts/feelings",
    46: "Avoidance of external reminders",
    47: "Inability to remember important aspect of traumatic event", 48: "Hyperarousal",
    49: "Preoccupation with having or acquiring serious illness", 50: "Sweating",
    51: "Trembling or shaking", 52: "Chest pain or discomfort",
    53: "Nausea or abdominal distress",
    54: "Feeling dizzy, unsteady, light-headed, or faint", 55: "Chills or heat sensations",
    56: "Paresthesias", 57: "Muscle tension",
    58: "Somatic symptoms causing disruption of daily life",
    59: "Excessive thoughts/feelings about somatic symptoms",
    60: "Altered voluntary motor or sensory function",
    61: "Derealization or depersonalization", 62: "Sleep disturbance",
    63: "Recurrent distressing dreams", 64: "Difficulty initiating sleep",
    65: "Difficulty maintaining sleep", 66: "Early morning wake", 67: "Excessive sleepiness",
    68: "Restriction of energy intake", 69: "Intense fear of gaining weight",
    70: "Persistent lack of recognition of low body weight", 71: "Binge eating",
    72: "Alcohol taken in larger amounts/longer period",
    73: "Persistent desire to cut down alcohol", 74: "Time spent to obtain/use alcohol",
    75: "Alcohol craving", 76: "Recurrent alcohol use in hazardous situations",
    77: "Alcohol tolerance", 78: "Alcohol withdrawal",
    79: "Alcohol use failing role obligations",
    80: "Substance taken in larger amounts/longer period",
    81: "Persistent desire to cut down substance", 82: "Time spent to obtain/use substance",
    83: "Substance craving", 84: "Recurrent substance use in hazardous situations",
    85: "Substance tolerance", 86: "Substance withdrawal",
    87: "Substance use failing role obligations",
    88: "Cognitive decline - memory/disorientation", 89: "Cognitive decline - attention",
    90: "Cognitive decline - executive function", 91: "Cognitive decline - language",
    92: "Cognitive decline - visuospatial function", 93: "Cognitive decline - social cognition",
    94: "Disturbance develops over short period",
    95: "Tends to fluctuate in severity during day", 96: "Enduring pattern - cognition",
    97: "Enduring pattern - affectivity", 98: "Enduring pattern - interpersonal functioning",
    99: "Enduring pattern - impulse control", 100: "Suicidal ideation/attempt/plan",
    101: "Abnormal contraction of muscles", 102: "Restlessness with excessive movements",
    103: "Involuntary or choreiform movements", 104: "Stress-related", 105: "Medication-related",
}
DOMAINS = [
    ("Psychotic", 1, 9), ("Manic", 10, 17), ("Obsessive-Compulsive", 18, 19),
    ("Depressive", 20, 28), ("Anxiety", 29, 40), ("Behavioral", 41, 42), ("Trauma", 43, 48),
    ("Illness anxiety", 49, 49), ("Somatic", 50, 57), ("Somatic symptoms disorder", 58, 59),
    ("Conversion and dissociative", 60, 61), ("Sleep", 62, 67), ("Eating", 68, 71),
    ("Alcohol use", 72, 79), ("Substance use", 80, 87), ("Cognition", 88, 95),
    ("Personality", 96, 99), ("Suicidality", 100, 100), ("Movement", 101, 103),
    ("Others (stress/medication)", 104, 105),
]

# ---------------------------------------------------------------- invented phrase bank
# code -> list of (Korean, English) invented sentences
BANK = {
    1: [("옆집 사람이 자기 물건을 가져가려 한다고 굳게 믿음", "firmly believes the people next door want to take their belongings"),
        ("집 안에 도청 장치가 있다고 확신함", "is convinced the house is bugged")],
    2: [("아무도 없는데 말소리가 들린다고 함", "hears voices when nobody is there"),
        ("벽에서 낯선 얼굴이 보인다고 함", "sees unfamiliar faces on the wall")],
    3: [("대화가 이어지지 않고 말이 뒤섞임", "speech is jumbled and hard to follow"),
        ("질문과 상관없는 이야기를 계속함", "keeps talking about unrelated things")],
    4: [("이유 없이 옷을 겹겹이 껴입고 돌아다님", "wanders wearing layers of clothes for no reason")],
    5: [("말수가 줄고 표정 변화가 거의 없음", "speaks little with almost no change in expression"),
        ("씻지 않고 하루 종일 누워 지냄", "lies in bed all day without washing")],
    10: [("자신이 큰 사업가라고 주장함", "claims to be a great businessman"),
         ("특별한 능력이 있다고 자랑함", "boasts of having a special ability")],
    11: [("기분이 들떠 있고 사소한 일에 크게 화를 냄", "elated mood and angry over small things")],
    12: [("밤새 여러 계획을 세우고 쉬지 않고 움직임", "makes many plans through the night and keeps moving")],
    13: [("이틀간 거의 자지 않았는데 피곤하지 않다고 함", "has hardly slept for two days but is not tired")],
    14: [("말이 쉬지 않고 이어져 끊기가 어려움", "talks nonstop and is hard to interrupt")],
    15: [("생각이 너무 빨리 넘어간다고 호소함", "reports thoughts racing too fast")],
    16: [("주변 소리에 계속 주의가 흐트러짐", "easily distracted by surrounding sounds")],
    17: [("충동적으로 큰돈을 쓰고 위험하게 운전함", "spends large sums impulsively and drives recklessly")],
    18: [("머릿속에서 같은 숫자를 계속 세게 되어 힘들어함", "struggles with counting the same numbers over and over in the head")],
    19: [("문이 잠겼는지 여러 번 확인함", "checks many times whether the door is locked")],
    20: [("온종일 마음이 무겁고 처져 있다고 말함", "says the mood stays heavy and flat through the whole day"),
         ("울적한 상태가 몇 주 이어짐", "low spirits that have lasted a few weeks")],
    21: [("예전에 즐기던 일에 흥미가 없어졌다고 함", "lost interest in things once enjoyed")],
    22: [("식욕이 크게 줄어 몇 달 새 몸무게가 빠졌다고 함", "appetite fell sharply and weight dropped in a few months")],
    23: [("몸이 처지고 말과 행동이 느려짐", "slowed speech and movement"),
         ("안절부절못하고 계속 서성임", "restless and keeps pacing")],
    24: [("기운이 없고 쉽게 지친다고 함", "low energy and tires easily")],
    25: [("자신이 가족에게 짐이 된다고 자책함", "blames self as a burden to the family")],
    26: [("집중이 안 되고 작은 결정도 못 내림", "cannot concentrate or make small decisions")],
    27: [("자신감이 바닥이라 사람 만나기를 꺼림", "confidence is at its lowest and avoids meeting people")],
    28: [("앞으로도 나아질 가능성이 없다고 말함", "says things will not get better")],
    29: [("높은 곳에 가면 극심하게 두려워함", "intensely afraid in high places")],
    31: [("사람 많은 곳에서 심하게 긴장하고 피함", "very tense in crowds and avoids them")],
    32: [("갑자기 심장이 쿵쾅대며 숨쉬기가 힘들어짐", "heart suddenly thumping hard with trouble breathing")],
    33: [("가슴 위에 무언가 눌린 듯 숨이 안 쉬어진다고 함", "feels as if something presses on the chest and cannot breathe")],
    39: [("작은 일에도 걱정이 많고 불안해함", "worries a lot and feels anxious about small things"),
         ("매사에 불안하고 걱정이 떠나지 않는다고 함", "anxious about everything and cannot shake the worries")],
    40: [("걱정을 스스로 멈추지 못한다고 함", "cannot stop worrying on their own")],
    41: [("물건을 던지며 심하게 화를 냄", "throws objects in a rage")],
    42: [("짜증이 늘고 쉽게 예민해짐", "more irritable and easily upset")],
    43: [("사고 장면이 계속 떠올라 괴롭다고 함", "keeps recalling the accident scene")],
    48: [("작은 소리에도 깜짝 놀라고 긴장함", "startles and tenses at small sounds")],
    49: [("자신이 중한 병에 걸린 것 같다며 같은 검사를 거듭 요청함", "thinks they have a severe disease and keeps requesting the same tests")],
    52: [("가슴이 답답하고 아프다고 호소함", "complains of chest tightness and pain")],
    53: [("속이 울렁거리고 배 안이 불편하다고 호소함", "queasy with an uneasy stomach")],
    54: [("어지럽고 머리가 멍하다고 함", "dizzy and light-headed")],
    57: [("목과 어깨가 계속 뻣뻣하다고 함", "neck and shoulders feel stiff all the time")],
    58: [("몸의 증상 때문에 일상생활이 어렵다고 함", "daily life disrupted by bodily symptoms")],
    59: [("몸의 증상 생각이 하루 종일 떠나지 않음", "bodily symptoms occupy their thoughts all day")],
    60: [("갑자기 한쪽 팔에 힘이 빠져 움직이지 못함", "sudden weakness of one arm")],
    62: [("잠을 제대로 못 잔다고 함", "not sleeping well")],
    64: [("잠들기까지 오래 걸린다고 함", "takes a long time to fall asleep")],
    65: [("자다가 자주 깨서 다시 잠들지 못함", "wakes often and cannot go back to sleep")],
    66: [("새벽 일찍 깨서 잠을 이루지 못함", "wakes very early and cannot sleep again")],
    67: [("낮에도 계속 졸리고 누워 있으려 함", "sleepy during the day and wants to lie down")],
    72: [("술을 예정보다 오래 많이 마심", "drinks more and longer than intended")],
    88: [("방금 한 일을 자꾸 잊어버림", "keeps forgetting what they just did")],
    98: [("가까운 사람들과 관계가 자주 틀어짐", "relationships with close people often break down")],
    99: [("충동을 참지 못하고 즉흥적으로 행동함", "cannot hold back impulses and acts on the spur of the moment")],
    100: [("삶을 끝내고 싶다는 마음이 자주 든다고 함", "often feels a wish to end their life"),
          ("약을 한꺼번에 먹고 자해를 시도함", "attempted self-harm by taking pills at once")],
    104: [("직장 문제로 스트레스를 많이 받았다고 함", "under heavy stress from problems at work")],
    105: [("처방받은 약을 임의로 끊은 뒤 악화됨", "stopped prescribed medication alone and got worse")],
}
PRE = [("", ""), ("최근 ", "recently, "), ("입원 전부터 ", "since before admission, "),
       ("며칠 전부터 ", "for several days, "), ("한 달 가까이 ", "for almost a month, ")]

# ---------------------------------------------------------------- group profiles (code -> weight)
MDD = {20: 6, 21: 4, 22: 3, 62: 3, 64: 2, 65: 2, 66: 1.5, 23: 2, 24: 4, 25: 3, 26: 3, 27: 2,
       28: 3, 100: 4, 42: 1.5, 39: 2.5, 104: 1, 105: 0.5}
MDD_AD = {**MDD, 39: 6, 40: 2, 32: 1}
PROFILE = {
    "MDD": MDD, "MDD_AD": MDD_AD,
    "SCZ": {1: 6, 2: 6, 3: 5, 4: 3, 5: 4, 62: 2, 100: 1.5, 105: 2, 42: 1.5, 41: 1, 88: 0.5,
            18: 0.5, 20: 0.5, 39: 1.5},
    "BIP": {10: 4, 11: 5, 12: 4, 13: 4, 14: 4, 15: 3, 16: 2, 17: 3, 42: 2, 20: 1.5, 62: 1.5,
            100: 1, 1: 0.7, 41: 1, 39: 2},
    "SOM": {49: 4, 52: 3, 53: 2, 54: 3, 57: 2, 58: 4, 59: 3, 60: 0.5, 62: 2, 39: 3, 32: 1.5, 20: 1},
    "ANX": {29: 2, 31: 2, 32: 3, 33: 2, 39: 5, 40: 3, 62: 2, 48: 1},
    "OTH": {99: 4, 98: 3, 41: 3, 42: 3, 100: 3, 20: 1.5, 72: 2, 104: 2, 39: 3},
}

# (profile, first-listed diagnosis, number of patients)
MDD_DX = [
    ("MDD", "Major depressive disorder, recurrent, moderate"),
    ("MDD", "Major depressive disorder, single episode, mild"),
    ("MDD", "Major depressive disorder, recurrent, severe with mood-congruent psychotic features"),
    ("MDD", "Major depressive disorder, single episode, moderate"),
    ("MDD_AD", "Major depressive disorder, single episode, severe with anxious distress"),
    ("MDD_AD", "Major depressive disorder, recurrent, severe with anxious distress"),
    ("MDD_AD", "Major depressive disorder, recurrent, moderate with anxious distress"),
    ("MDD_AD", "Major depressive disorder, single episode, moderate with anxious distress"),
]
SCZ_DX = ["Schizophrenia", "Schizophrenia, first episode, currently in acute episode",
          "Schizophrenia, multiple episodes, currently in acute episode",
          "Schizophrenia, multiple episodes, currently in acute episode",
          "Schizophrenia, continuous", "Schizophrenia, first episode, currently in acute episode"]
BIP_DX = ["Bipolar I disorder, current episode manic, severe",
          "Bipolar I disorder, current episode manic, moderate",
          "Bipolar II disorder, current episode depressed",
          "Bipolar I disorder, current episode manic, severe"]
COMORBID = ["Generalized anxiety disorder", "Panic disorder", "Alcohol use disorder",
            "Obsessive-compulsive disorder", "Nicotine use disorder"]


def tag(dx):
    """Mark every diagnosis string as invented."""
    return f"{dx} (synthetic)" if dx else ""


def build():
    rng = np.random.default_rng(SEED)
    plan = ([(p, dx) for p, dx in MDD_DX] + [("SCZ", d) for d in SCZ_DX]
            + [("BIP", d) for d in BIP_DX]
            + [("SOM", "Undifferentiated somatoform disorder"), ("SOM", "Somatic symptom disorder, with predominant pain"),
               ("ANX", "Panic disorder"), ("OTH", "Borderline personality disorder")])
    rows = []
    patients = []
    for prof, dx1 in plan:
        k = rng.choice([0, 1, 2], p=[0.55, 0.30, 0.15])
        dx2, dx3 = (list(rng.choice(COMORBID, size=k, replace=False)) + ["", ""])[:2] if k else ("", "")
        patients.append((prof, dx1, dx2, dx3, False))
    # two patients that the cohort rules remove (protocol exclusion; invalid label)
    patients.append(("MDD", "Major depressive disorder, recurrent, mild", "Intellectual disability, moderate", "", False))
    patients.append(("SCZ", "Schizophrenia, continuous", "", "", True))
    order = rng.permutation(len(patients))
    patients = [patients[i] for i in order]
    for i in range(1, len(patients)):          # neighbouring patients must differ in (dx1, dx2, dx3)
        while patients[i][1:4] == patients[i - 1][1:4]:
            j = int(rng.integers(len(patients)))
            patients[i], patients[j] = patients[j], patients[i]
    for prof, dx1, dx2, dx3, bad_label in patients:
        w = PROFILE[prof]
        codes = np.array(list(w))
        p = np.array(list(w.values()), dtype=float)
        p /= p.sum()
        n = int(rng.integers(8, 15))
        for s in range(n):
            main = [int(rng.choice(codes, p=p))]
            if rng.random() < 0.12:
                main.append(int(rng.choice(codes, p=p)))
            main = sorted(set(main))
            parts = [BANK[c][int(rng.integers(len(BANK[c])))] for c in main]
            pre = PRE[int(rng.integers(len(PRE)))]
            ko = pre[0] + ", ".join(x[0] for x in parts)
            en = pre[1] + "; ".join(x[1] for x in parts)
            label_a = "; ".join(map(str, main))
            label_b = ""
            if rng.random() < 0.08:
                label_b = str(int(rng.choice(codes, p=p)))
            if bad_label and s == 0:
                label_a = "106"
            rows.append((tag(dx1), tag(dx2), tag(dx3), ko, en, label_a, label_b))
    cols = ["dx1", "dx2", "dx3", "cp_korean", "cp_english", "label_a", "label_b"]
    return pd.DataFrame(rows, columns=cols)


def codebook():
    out = []
    for name, lo, hi in DOMAINS:
        out += [(c, name, ITEMS[c]) for c in range(lo, hi + 1)]
    return pd.DataFrame(out, columns=["code", "domain", "item"])


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    df = build()
    df.to_csv(OUT / "synthetic_chief_problems.csv", index=False, encoding="utf-8-sig")
    codebook().to_csv(OUT / "codebook.csv", index=False, encoding="utf-8-sig")
    key = df.dx1 + "|" + df.dx2 + "|" + df.dx3
    print(len(df), "sentences;", int((key != key.shift()).sum()), "patients")
