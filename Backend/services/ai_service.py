import json
from google import genai
from django.conf import settings
from django.utils import timezone
from tenacity import retry, stop_after_attempt, wait_exponential


client = genai.Client(api_key=settings.GEMINI_API_KEY)


def build_prompt(topic, difficulty, count):
    topic_path = topic.get_full_path()
    difficulty_instructions = {
        'easy':   'basic conceptual questions suitable for beginners',
        'medium': 'intermediate questions requiring applied knowledge',
        'hard':   'advanced questions requiring deep understanding',
    }
    instruction = difficulty_instructions.get(difficulty, 'intermediate questions')

    return f"""Generate exactly {count} multiple choice questions about "{topic_path}".
Difficulty level: {difficulty} — {instruction}.

Return ONLY a valid JSON array. No explanation, no markdown, no code blocks.
Each object must have exactly these fields:
{{
    "question": "the question text",
    "explanation": "why the correct answer is right",
    "choices": [
        {{"text": "option A", "is_correct": false}},
        {{"text": "option B", "is_correct": true}},
        {{"text": "option C", "is_correct": false}},
        {{"text": "option D", "is_correct": false}}
    ]
}}

Rules:
- Exactly 4 choices per question
- Exactly 1 correct choice per question
- No duplicate questions
- Questions must be specific to {topic_path}
- Return only the JSON array, nothing else"""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_gemini(prompt):
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
    )
    return response.text


def parse_gemini_response(raw_text):
    text = raw_text.strip()

    if text.startswith('```'):
        lines = text.split('\n')
        text  = '\n'.join(lines[1:-1])

    text = text.strip()

    try:
        questions = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {e}")

    if not isinstance(questions, list):
        raise ValueError("Gemini response is not a JSON array")

    validated = []
    for i, q in enumerate(questions):
        if 'question' not in q or 'choices' not in q:
            raise ValueError(f"Question {i+1} missing required fields")

        choices  = q['choices']
        correct  = [c for c in choices if c.get('is_correct')]
        if len(correct) != 1:
            raise ValueError(
                f"Question {i+1} must have exactly 1 correct choice"
            )
        if len(choices) != 4:
            raise ValueError(
                f"Question {i+1} must have exactly 4 choices"
            )

        validated.append({
            'text':        q['question'],
            'explanation': q.get('explanation', ''),
            'choices':     choices,
        })

    return validated


def deduplicate_questions(questions, topic_id):
    from apps.quizzes.models import Question
    existing_texts = set(
        Question.objects.filter(
            quiz__topic_id=topic_id,
            is_deleted=False
        ).values_list('text', flat=True)
    )
    return [
        q for q in questions
        if q['text'].strip() not in existing_texts
    ]


def save_generated_questions(quiz, questions):
    from apps.quizzes.models import Question, Choice

    for order, q_data in enumerate(questions, start=1):
        question = Question.objects.create(
            quiz=quiz,
            text=q_data['text'],
            explanation=q_data.get('explanation', ''),
            order=order,
            marks=1.0,
        )
        for choice_order, c_data in enumerate(q_data['choices'], start=1):
            Choice.objects.create(
                question=question,
                text=c_data['text'],
                is_correct=c_data.get('is_correct', False),
                order=choice_order,
            )


def generate_quiz_questions(request_id):
    from apps.ai_generation.models import AIGenerationRequest
    from apps.quizzes.models import Quiz

    try:
        ai_request = AIGenerationRequest.objects.select_related(
            'topic', 'requested_by'
        ).get(id=request_id)
    except AIGenerationRequest.DoesNotExist:
        return False

    ai_request.status = 'processing'
    ai_request.save()

    try:
        prompt = build_prompt(
            topic=ai_request.topic,
            difficulty=ai_request.difficulty,
            count=ai_request.question_count,
        )
        ai_request.prompt_used = prompt
        ai_request.save()

        raw_response = call_gemini(prompt)

        ai_request.raw_response = {'text': raw_response}
        ai_request.save()

        questions = parse_gemini_response(raw_response)
        questions = deduplicate_questions(questions, ai_request.topic_id)

        if not questions:
            raise ValueError('All generated questions were duplicates')

        quiz = Quiz.objects.create(
            title=f"{ai_request.topic.name} — {ai_request.difficulty.title()} Quiz",
            topic=ai_request.topic,
            difficulty=ai_request.difficulty,
            total_questions=len(questions),
            is_published=True,
            is_ai_generated=True,
            created_by=ai_request.requested_by,
        )

        save_generated_questions(quiz, questions)

        ai_request.status       = 'completed'
        ai_request.quiz         = quiz
        ai_request.completed_at = timezone.now()
        ai_request.save()

        return True

    except Exception as e:
        import traceback
        print("FULL ERROR:", traceback.format_exc())
        ai_request.status        = 'failed'
        ai_request.error_message = str(e)
        ai_request.retries      += 1
        ai_request.save()
        return False