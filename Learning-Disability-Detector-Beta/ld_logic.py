def evaluate_dyslexia(answers):
    # Simple answer key for demo purposes
    correct = ['b','b','a','a','b']
    score = sum(1 for a,c in zip(answers, correct) if a==c)
    return {
        'type': 'Dyslexia',
        'score': score,
        'flag': score < 3,
        'message': 'Possible signs of dyslexia' if score < 3 else 'No major signs detected.'
    }

def evaluate_dyscalculia(answers, targets=None):
    """Evaluate phonetic spelling (used under Dyscalculia route as Phonetics).
    Compares typed answers to provided targets (correct English spellings),
    case-insensitive exact match.
    """
    targets = targets or []
    total = len(targets)
    score = 0
    for i in range(total):
        a = (answers[i] if i < len(answers or []) else '')
        t = (targets[i] if i < len(targets) else '')
        if (a or '').strip().lower() == (t or '').strip().lower():
            score += 1

    flag = score < 3  # keep threshold consistent with previous demo logic
    message = (
        'Consider practicing phonics and spelling patterns' if flag
        else 'Spelling patterns appear within typical range.'
    )

    return {
        'type': 'Dyscalculia',
        'score': score,
        'flag': flag,
        'message': message
    }

def _edits_leq_one(a: str, b: str) -> bool:
    """Return True if a and b are equal under case-insensitive comparison
    allowing at most one edit (insert/delete/substitute)."""
    a = (a or '').strip().lower()
    b = (b or '').strip().lower()

    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False

    # Two-pointer check for <=1 edit
    i = j = 0
    diff = 0
    while i < la and j < lb:
        if a[i] == b[j]:
            i += 1
            j += 1
        else:
            if diff == 1:
                return False
            diff += 1
            if la == lb:
                # substitution
                i += 1
                j += 1
            elif la > lb:
                # deletion in a
                i += 1
            else:
                # insertion in a (i.e., deletion in b)
                j += 1

    # Account for trailing char
    if i < la or j < lb:
        diff += 1
    return diff <= 1


def evaluate_memory(recall_list, target_list):
    """Evaluate nonword repetition by comparing each recall with the corresponding target.
    Case-insensitive, allow edit distance <= 1.
    """
    total = len(target_list or [])
    correct = 0

    for idx in range(total):
        target = (target_list[idx] if idx < len(target_list) else '')
        ans = (recall_list[idx] if idx < len(recall_list or []) else '')
        if _edits_leq_one(ans, target):
            correct += 1

    # Dynamic flag threshold: below half indicates potential challenge
    threshold = total // 2 if total > 0 else 0
    flag = correct < threshold
    message = (
        'Possible working memory challenges' if flag
        else 'Working memory within typical range.'
    )

    return {
        'type': 'Working Memory',
        'score': correct,
        'total': total,
        'flag': flag,
        'message': message
    }


def evaluate_phonetics(spell_list, target_list, level_list=None):
    """Evaluate phonetic spelling with per-level breakdown.
    - Case-insensitive exact match (educational, not diagnostic).
    - Returns score, total, per-level counts, and an educational message.
    """
    spell_list = spell_list or []
    target_list = target_list or []
    level_list = level_list or []

    # Normalize inputs lengths
    n = min(len(target_list), len(spell_list))
    total = n
    # Count per level (1,2,3)
    per_level_total = {1: 0, 2: 0, 3: 0}
    per_level_correct = {1: 0, 2: 0, 3: 0}

    for i in range(n):
        # Determine level for this item
        try:
            lvl = int(level_list[i]) if i < len(level_list) else 1
        except Exception:
            lvl = 1
        if lvl not in per_level_total:
            lvl = 1
        per_level_total[lvl] += 1

        # Compare case-insensitive
        student = (spell_list[i] or '').strip().lower()
        target = (target_list[i] or '').strip().lower()
        if student == target:
            per_level_correct[lvl] += 1

    score = sum(per_level_correct.values())
    # Educational message with per-level breakdown
    l1 = f"Level 1: {per_level_correct[1]}/{per_level_total[1]}"
    l2 = f"Level 2: {per_level_correct[2]}/{per_level_total[2]}"
    l3 = f"Level 3: {per_level_correct[3]}/{per_level_total[3]}"
    message = (
        f"Phonetic spelling overview — {l1}, {l2}, {l3}. "
        "This activity explores how sounds connect to English spelling patterns."
    )

    # Flag below half as potential area to practice (educational tone)
    threshold = total // 2 if total > 0 else 0
    flag = score < threshold

    return {
        'type': 'Phonetics',
        'score': score,
        'total': total,
        'flag': flag,
        'message': message,
        'level_breakdown': {
            'level1': {'correct': per_level_correct[1], 'total': per_level_total[1]},
            'level2': {'correct': per_level_correct[2], 'total': per_level_total[2]},
            'level3': {'correct': per_level_correct[3], 'total': per_level_total[3]},
        }
    }


def evaluate_phonetics_legacy_mcq(answers):
    """Legacy 5-item multiple-choice fallback evaluator.
    Uses a simple answer key for backwards compatibility only.
    """
    correct_key = ['c', 'b', 'a', 'a', 'b']
    score = sum(1 for a, c in zip(answers or [], correct_key) if (a or '').strip().lower() == c)
    total = len(correct_key)
    flag = score < 3
    message = (
        "Legacy phonetic items scored. For the new phonetic spelling, responses are typed "
        "words with increasing complexity across three levels."
    )
    return {
        'type': 'Phonetics',
        'score': score,
        'total': total,
        'flag': flag,
        'message': message
    }
