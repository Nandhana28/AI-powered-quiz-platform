import factory
from django.contrib.auth import get_user_model
from apps.quizzes.models import Topic, Quiz, Question, Choice
from apps.attempts.models import QuizAttempt

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email    = factory.Sequence(lambda n: f'user{n}@test.com')
    password = factory.PostGenerationMethodCall('set_password', 'Test1234!')
    role     = 'user'


class TopicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Topic

    name  = factory.Sequence(lambda n: f'Topic {n}')
    slug  = factory.Sequence(lambda n: f'topic-{n}')
    level = 3


class QuizFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Quiz

    title      = factory.Sequence(lambda n: f'Quiz {n}')
    topic      = factory.SubFactory(TopicFactory)
    difficulty = 'easy'
    is_published = True


class QuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Question

    quiz  = factory.SubFactory(QuizFactory)
    text  = factory.Sequence(lambda n: f'Question {n}?')
    order = factory.Sequence(lambda n: n)
    marks = 1.0


class ChoiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Choice

    question   = factory.SubFactory(QuestionFactory)
    text       = factory.Sequence(lambda n: f'Choice {n}')
    is_correct = False
    order      = factory.Sequence(lambda n: n)