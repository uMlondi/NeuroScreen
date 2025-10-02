import random

# ========= PASSAGE TEXTS =========
PASSAGES = {
    "procrastination": """The Procrastination Puzzle: Why We Delay (and How to Break Free)
We’ve all been there. A big deadline is coming up, and you swear you’re about to start. You open a blank document, maybe even type a title… then suddenly you’re on your phone, convincing yourself that scrolling for “just five minutes” won’t hurt. Before you know it, the day is gone and you’re telling yourself, “I’ll start tomorrow. I work better under pressure anyway.”
That’s procrastination in action delaying what matters most even though deep down you know it’s going to cost you later.

Why We Really Procrastinate
For a long time, procrastination was seen as a lack of willpower or poor time management. But research now paints a different picture. It’s not about being lazy it’s about how we manage our emotions.
When a task feels boring, stressful, or overwhelming, our brains look for a quick escape. Checking social media or watching Netflix offers instant relief. The problem? The relief is temporary, while the stress of the undone task keeps building.
On top of that, your brain actually rewards you for avoiding work. Every time you procrastinate, you get a tiny hit of dopamine a “feel-good” chemical that trains your brain to repeat the cycle. That’s why procrastination feels so hard to break: it’s wired into your reward system.

The Vicious Cycle
Here’s how it usually goes:
You avoid the task → feel relief.
Relief is short-lived → guilt and anxiety creep in.
Pressure builds → you cram at the last minute.
You get it done but with extra stress, poor focus, and lower quality.
Sound familiar? That’s the procrastination loop.

How to Break the Cycle
The good news: procrastination isn’t a life sentence. With a few practical shifts, you can loosen its grip.

Try the “Just Five Minutes” Rule
Tell yourself you’ll only work for five minutes. Often, getting started is the hardest part and once you’re in, momentum carries you forward.

Focus on the Next Step, Not the Whole Project
Big goals can feel paralyzing. Instead of thinking, “I have to write this whole essay,” shrink it down: “I’ll just find three articles to read.” Small wins build momentum.

Be Kind to Yourself
Surprisingly, self-compassion is one of the best tools against procrastination. Beating yourself up makes you more likely to avoid tasks in the future. Forgiving yourself for past delays reduces guilt and frees you up to start fresh.

Final Thought
Procrastination isn’t proof that you’re lazy or broken. It’s a very human response to stress and discomfort. Once you understand that, you can start working with your brain instead of against it and finally get moving on the things that matter.
""",

    "perfectionism": """Perfectionism as Hidden Procrastination
You sit at your desk with every intention of finishing a report. Instead of typing, you spend twenty minutes adjusting the font, another half-hour rereading the introduction, and then an hour second-guessing whether your argument is strong enough. Progress feels invisible because nothing ever seems “good enough.” This is not productivity—it’s perfectionism, a hidden form of procrastination.
For many years, perfectionism was regarded as a sign of ambition or high standards. However, contemporary research has shown that excessive perfectionism is less about striving for excellence and more about managing fear—fear of failure, fear of criticism, and fear of falling short of expectations. The perfectionist avoids discomfort not by ignoring the task, but by endlessly polishing small details.
This behavior is reinforced in the brain in a way similar to procrastination. Each time a perfectionist avoids moving forward by obsessing over minor revisions, the brain rewards the temporary relief from anxiety. This creates a loop where the individual feels productive while actually remaining stagnant. The short-term comfort of fine-tuning disguises the long-term cost: unfinished projects, missed deadlines, and rising stress levels.

The cycle usually unfolds like this:
An important task begins with enthusiasm.
Doubts and self-criticism start to appear.
Small edits or corrections provide temporary relief.
Time runs out, leading to frustration and incomplete results.

Breaking free requires more than simply “trying harder.” Helpful strategies include:
Redefine Success: Instead of chasing flawlessness, focus on relevence—does the work achieve its purpose?
Set Time Limits: Allocate a fixed amount of time to each stage, forcing yourself to move forward instead of spiraling in revisions.
Practice Self-Distancing: Imagine advising a friend in the same situation. This perspective reduces the harshness of your own self-crticism.

Understanding perfectionism as a coping mechanism—rather than as proof of dedication—can shift the narrative. True growth is not about producing flawless work but about finishing meaningful work consistently. Only then does effort translate into real accomplisment.
""",

    "multitasking": """The Multitasking Myth
In today’s digital environment, the ability to juggle multiple tasks at once is often praised as a critical skill. Many individuals pride themselves on answering emails during meetings, listening to podcasts while studying, or switching rapidly between projects. Yet research consistently demonstrates that multitasking is less a sign of efficiency than a phenomenon of divided attention, producing more errors and reducing overall performance.
For decades, people assumed the human brain could process several streams of information simultaneously. Contemporary neuroscience, however, reveals that the brain does not truly multitask; it engages in task-switching, shifting attention rapidly from one focus to another. Each shift carries a hidden consequence: a loss of time, diminished accuracy, and increased mental fatigue. What feels like productivity is often merely the illusion of activity.
The rewards of multitasking are deceptive. Responding to an email while drafting a report may feel productive because the brain experiences a small rush of novelty. This novelty triggers a cognitive reward response, similar to the dopamine hit found in procrastination or perfectionism. The brain mistakes the stimulation for progress, even though genuine progress slows.
Over time, this pattern forms a damaging cycle:
Multitasking begins with the sense of efficiency and control.
Errors accumulate, requiring rework and lost effort.
Fatigue and stress intensify, lowering motivation.
Despite negative outcomes, the habit repeats because the novelty feels rewarding.

Breaking the cycle demands intentional strategies:
Single-Task Commitment: Dedicate focused blocks of time to one activity, resisting the urge to switch.
Mindful Transitions: Instead of abruptly changing tasks, pause deliberately to reset attention.
Value-Based Priorities: Determine which activities hold true significance, rather than scattering attention across trivial distractions.

Reframing multitasking not as a strength but as a costly cognitive trap allows individuals to reclaim focus. Sustainable productivity is not measured by how many tasks one touches, but by how deeply one engages with what truly matters.
"""
}

# ========= 30 QUESTIONS WITH PASSAGE TAGS =========
QUESTIONS = [
    # ----- Procrastination (1–10) -----
    {"id": 1, "passage": "procrastination", "text": "According to modern psychology, what is now considered the main reason people procrastinate?",
     "options": {
         "a": "Poor time management and weak planning skills.",
         "b": "Lack of discipline and personal strength.",
         "c": "Difficulty regulating emotions when tasks feel boring, stressful, or overwhelming.",
         "d": "Naturally short attention spans that make it impossible to sustain focus."},
     "answer": "c"},
    {"id": 2, "passage": "procrastination", "text": "In the opening example, after opening a blank document, what does the person end up doing?",
     "options": {
         "a": "Beginning the essay but quickly stopping after the first paragraph.",
         "b": "Checking their phone, convincing themselves it will only take five minutes.",
         "c": "Drafting a to-do list instead of starting the assignment.",
         "d": "Reviewing their notes to delay the actual writing."},
     "answer": "b"},
    {"id": 3, "passage": "procrastination", "text": "How does the brain reinforce procrastination, according to the passage?",
     "options": {
         "a": "By producing dopamine each time avoidance provides temporary relief.",
         "b": "By releasing cortisol to increase focus and urgency.",
         "c": "By lowering stress hormones whenever a task is completed.",
         "d": "By strengthening long-term memory during distractions."},
     "answer": "a"},
    {"id": 4, "passage": "procrastination", "text": "What emotional consequence follows the short-lived relief of avoiding a task?",
     "options": {
         "a": "Motivation increases and the person feels prepared to restart.",
         "b": "Guilt and anxiety begin to build, adding more stress.",
         "c": "Calmness returns, making the task easier to handle.",
         "d": "Determination and discipline are restored."},
     "answer": "b"},
    {"id": 5, "passage": "procrastination", "text": "In the procrastination loop described, what typically happens in the final stage?",
     "options": {
         "a": "The task is abandoned and never completed.",
         "b": "The task is completed last-minute, but with extra stress and lower quality.",
         "c": "The person feels so guilty they avoid the task even longer.",
         "d": "The task is completed perfectly but with little learning."},
     "answer": "b"},
    {"id": 6, "passage": "procrastination", "text": "What is the purpose of the “Just Five Minutes Rule”?",
     "options": {
         "a": "To divide work permanently into five-minute sessions.",
         "b": "To make tasks more enjoyable by limiting how long they last.",
         "c": "To trick the brain into starting, since momentum often makes continuing easier.",
         "d": "To delay tasks in smaller, more manageable ways."},
     "answer": "c"},
    {"id": 7, "passage": "procrastination", "text": "In the section about breaking down tasks, what specific example does the passage give?",
     "options": {
         "a": "Writing the introduction paragraph first.",
         "b": "Finding three articles to read as a smaller starting step.",
         "c": "Editing a previously completed section of the essay.",
         "d": "Creating an outline of the full essay before writing."},
     "answer": "b"},
    {"id": 8, "passage": "procrastination", "text": "How does self-compassion help people overcome procrastination?",
     "options": {
         "a": "It makes them feel guiltier, motivating them to work harder.",
         "b": "It reduces self-criticism, allowing forgiveness for past delays and lowering avoidance.",
         "c": "It increases pressure by emphasizing the cost of wasted time.",
         "d": "It distracts them from the stress of the task completely."},
     "answer": "b"},
    {"id": 9, "passage": "procrastination", "text": "In the conclusion, how does the passage reframe procrastination?",
     "options": {
         "a": "As proof of laziness and lack of willpower.",
         "b": "As a permanent personal weakness.",
         "c": "As a natural human response to stress and discomfort.",
         "d": "As an unavoidable flaw that cannot be managed."},
     "answer": "c"},
    {"id": 10, "passage": "procrastination", "text": "Which of the following best summarizes the passage’s overall message?",
     "options": {
         "a": "Procrastination is caused by poor planning and must be solved with strict discipline.",
         "b": "Procrastination is rooted in emotional regulation but can be managed with practical strategies like small steps, momentum, and self-compassion.",
         "c": "Procrastination is unavoidable but less damaging if people work well under pressure.",
         "d": "Procrastination is purely a chemical addiction that cannot be broken without medical treatment."},
     "answer": "b"},

    # ----- Perfectionism (11–20) -----
    {"id": 11, "passage": "perfectionism", "text": "According to the passage, what does research suggest is the deeper cause of excessive perfectionism?",
     "options": {
         "a": "A natural drive for achievement and excellence.",
         "b": "The need to manage fears of failure, criticism, and falling short.",
         "c": "Weak organizational and planning skills.",
         "d": "Genetic traits that make people detail-oriented."},
     "answer": "b"},
    {"id": 12, "passage": "perfectionism", "text": "In the introduction, how does the perfectionist behave while working on a report?",
     "options": {
         "a": "They polish minor details like font and reread sections instead of advancing the main work.",
         "b": "They rush to finish quickly, ignoring structure and clarity.",
         "c": "They complete the first draft immediately and then set it aside.",
         "d": "They avoid starting altogether and distract themselves with unrelated activities."},
     "answer": "a"},
    {"id": 13, "passage": "perfectionism", "text": "How is perfectionism reinforced in the brain, according to the text?",
     "options": {
         "a": "The brain rewards temporary relief from anxiety when small edits replace progress.",
         "b": "The brain strengthens memory each time details are polished.",
         "c": "The brain reduces cortisol levels when people delay difficult tasks.",
         "d": "The brain encourages multitasking, which gives a sense of control."},
     "answer": "a"},
    {"id": 14, "passage": "perfectionism", "text": "In the perfectionism cycle described, what typically happens in the final stage?",
     "options": {
         "a": "Time runs out, leading to frustration and incomplete results.",
         "b": "The task is restarted repeatedly until flawless.",
         "c": "The work is abandoned entirely without attempting completion.",
         "d": "The project is finished perfectly but creates exhaustion."},
     "answer": "a"},
    {"id": 15, "passage": "perfectionism", "text": "Why does the passage suggest redefining success as an effective strategy?",
     "options": {
         "a": "It prevents mistakes by encouraging stricter standards.",
         "b": "It shifts focus from flawlessness to whether the work achieves its purpose.",
         "c": "It reduces workload by allowing tasks to be skipped entirely.",
         "d": "It ensures productivity by forcing comparison with others."},
     "answer": "b"},
    {"id": 16, "passage": "perfectionism", "text": "How do time limits help break the cycle of perfectionism?",
     "options": {
         "a": "They create external pressure that forces panic and productivity.",
         "b": "They encourage multitasking to finish more quickly.",
         "c": "They prevent endless revisions by requiring forward movement.",
         "d": "They reduce anxiety by lowering expectations for the work."},
     "answer": "c"},
    {"id": 17, "passage": "perfectionism", "text": "What is the main purpose of self-distancing as a strategy?",
     "options": {
         "a": "To make individuals detach completely from their work.",
         "b": "To imagine giving advice to a friend, reducing harsh self-criticism.",
         "c": "To increase external feedback and accountability.",
         "d": "To motivate people to restart tasks with greater urgency."},
     "answer": "b"},
    {"id": 18, "passage": "perfectionism", "text": "In the conclusion, how does the passage reframe perfectionism?",
     "options": {
         "a": "As proof of strong ambition and dedication.",
         "b": "As a coping mechanism rather than true productivity.",
         "c": "As a weakness that prevents people from achieving success.",
         "d": "As a natural personality trait that cannot be changed."},
     "answer": "b"},
    {"id": 19, "passage": "perfectionism", "text": "What similarity does the passage highlight between perfectionism and procrastination?",
     "options": {
         "a": "Both involve avoiding tasks by turning to entertainment.",
         "b": "Both offer temporary emotional relief while delaying true progress.",
         "c": "Both guarantee higher-quality results in the long run.",
         "d": "Both depend mainly on external deadlines to function."},
     "answer": "b"},
    {"id": 20, "passage": "perfectionism", "text": "Which of the following best summarizes the overall message of the passage?",
     "options": {
         "a": "Perfectionism is simply a form of ambition that should be encouraged.",
         "b": "Perfectionism is a harmless habit that improves detail-oriented work.",
         "c": "Perfectionism, like procrastination, is a coping strategy that provides short-term relief but harms long-term outcomes, and can be managed with strategies like redefining success, time limits, and self-distancing.",
         "d": "Perfectionism is unavoidable and must be accepted as part of human productivity"},
     "answer": "c"},

    # ----- Multitasking (21–30) -----
    {"id": 21, "passage": "multitasking", "text": "According to the passage, how does research actually describe multitasking?",
     "options": {
         "a": "As an efficient skill where the brain processes information in parallel.",
         "b": "As a phenomenon of divided attention, leading to more mistakes and lower performance.",
         "c": "As an ability that only works effectively for simple tasks.",
         "d": "As a natural talent confirmed by scientific studies."},
     "answer": "b"},
    {"id": 22, "passage": "multitasking", "text": "What does neuroscience reveal about what the brain does when we think we are multitasking?",
     "options": {
         "a": "It processes multiple streams of input simultaneously.",
         "b": "It rapidly shifts focus between tasks, engaging in task-switching.",
         "c": "It strengthens memory capacity to handle diverse information.",
         "d": "It filters distractions while maintaining efficiency."},
     "answer": "b"},
    {"id": 23, "passage": "multitasking", "text": "What are the hidden consequences of task-switching?",
     "options": {
         "a": "Increased speed and higher efficiency in all areas.",
         "b": "Reduced time efficiency, lower accuracy, and more mental fatigue.",
         "c": "Fewer errors but greater reliance on working memory.",
         "d": "Stronger motivation with less focus on quality."},
     "answer": "b"},
    {"id": 24, "passage": "multitasking", "text": "Why does multitasking feel productive to many people, despite slowing progress?",
     "options": {
         "a": "Because external approval reinforces multitasking as a cultural norm.",
         "b": "Because novelty creates a cognitive reward response that feels like progress.",
         "c": "Because multitasking prevents boredom by moving attention constantly.",
         "d": "Because switching tasks allows faster completion overall."},
     "answer": "b"},
    {"id": 25, "passage": "multitasking", "text": "In the multitasking cycle described in the passage, what occurs during the second stage?",
     "options": {
         "a": "Errors accumulate, leading to extra corrections and lost effort.",
         "b": "Motivation increases as tasks become more engaging.",
         "c": "Stress decreases due to stimulation from novelty.",
         "d": "Work is completed faster with fewer mistakes."},
     "answer": "a"},
    {"id": 26, "passage": "multitasking", "text": "Which strategy is highlighted as Single-Task Commitment?",
     "options": {
         "a": "Pausing deliberately before task changes to reset attention.",
         "b": "Focusing on one task in dedicated time blocks, resisting the urge to switch.",
         "c": "Ranking activities by their long-term signifigance.",
         "d": "Removing all distractions by multitasking in structured cycles."},
     "answer": "b"},
    {"id": 27, "passage": "multitasking", "text": "Why does the author emphasize mindful transitions?",
     "options": {
         "a": "To make switching more frequent and less noticeable.",
         "b": "To pause deliberately, helping attention reset between tasks.",
         "c": "To reduce stress by avoiding tasks altogether.",
         "d": "To increase efficiency by multitasking in short bursts."},
     "answer": "b"},
    {"id": 28, "passage": "multitasking", "text": "How is multitasking reframed in the conclusion?",
     "options": {
         "a": "As a permanent human skill that improves with practice.",
         "b": "As a costly cognitive trap that reduces true focus.",
         "c": "As a natural coping mechanism for stress and anxiety.",
         "d": "As a useful habit that simply needs balance."},
     "answer": "b"},
    {"id": 29, "passage": "multitasking", "text": "What connection is drawn between multitasking, procrastination, and perfectionism?",
     "options": {
         "a": "All three provide short-term brain rewards while harming long-term progress.",
         "b": "All three strengthen discipline and create sustainable motivation.",
         "c": "All three improve productivity under strict deadlines.",
         "d": "All three occur only when external accountability is missing."},
     "answer": "a"},
    {"id": 30, "passage": "multitasking", "text": "Which of the following best summarizes the central idea of the passage?",
     "options": {
         "a": "Multitasking increases productivity by keeping the brain stimulated with novelty.",
         "b": "Multitasking is not true efficiency but task-switching, which leads to mistakes, fatigue, and slower progress, and can be improved by focusing strategies.",
         "c": "Multitasking is a natural strength that should be embraced in modern digital environments.",
         "d": "Multitasking is only harmful when combined with procrastination or perfectionism."},
     "answer": "b"},
]


PASSAGE_TITLES = {
    "procrastination": "The Procrastination Puzzle",
    "perfectionism": "Perfectionism as Hidden Procrastination",
    "multitasking": "The Multitasking Myth",
}

LEVEL_PASSAGES = {
    "easy": ["procrastination"],
    "medium": ["perfectionism"],
    "hard": ["multitasking"],
}


def get_questions_for_difficulty(difficulty, seed=None):
    """Return passages/questions configured for a given difficulty."""
    difficulty = (difficulty or "").lower()
    if difficulty not in LEVEL_PASSAGES:
        raise ValueError(f"Unsupported difficulty '{difficulty}'")

    rng = random.Random(seed)
    grouped = {}

    for passage_key in LEVEL_PASSAGES[difficulty]:
        pool = [q.copy() for q in QUESTIONS if q["passage"] == passage_key]

        if len(pool) >= 5:
            chosen = rng.sample(pool, k=5)
        else:
            chosen = pool  # fallback if fewer than 5 questions are available

        for q in chosen:
            items = list(q["options"].items())
            items.sort(key=lambda kv: kv[0])  # consistent option order a-d
            q["options_shuffled"] = items

        grouped[passage_key] = {
            "text": PASSAGES.get(passage_key, ""),
            "questions": chosen,
            "title": PASSAGE_TITLES.get(passage_key, passage_key.title())
        }

    return {
        "difficulty": difficulty,
        "blocks": grouped
    }
