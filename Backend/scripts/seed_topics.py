import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.quizzes.models import Topic
from django.utils.text import slugify

TOPIC_TREE = {
    "Computer Science": {
        "Frontend":   ["HTML & CSS", "JavaScript", "React", "TypeScript"],
        "Backend":    ["Django", "REST APIs", "System Design", "Node.js"],
        "Core CS":    ["OOPS", "DBMS", "Operating Systems", "Computer Networks"],
        "Languages":  ["C++", "Python", "Java", "C"],
        "DSA":        ["Arrays & Strings", "Linked Lists", "Trees & Graphs",
                       "Sorting & Searching", "Dynamic Programming", "Recursion"],
        "Software":   ["Design Patterns", "Git & Version Control",
                       "Testing", "Agile & Scrum"],
    },
    "Mathematics": {
        "Pure Math":        ["Algebra", "Calculus", "Number Theory",
                             "Geometry", "Trigonometry"],
        "Applied Math":     ["Statistics", "Probability",
                             "Linear Algebra", "Discrete Math"],
        "Competitive Math": ["Combinatorics", "Graph Theory"],
    },
    "Chemistry": {
        "Organic":   ["Hydrocarbons", "Reactions & Mechanisms",
                      "Functional Groups", "Polymers"],
        "Inorganic": ["Periodic Table", "Chemical Bonding",
                      "Coordination Chemistry"],
        "Physical":  ["Thermodynamics", "Chemical Kinetics",
                      "Electrochemistry", "Equilibrium"],
    },
    "Physics": {
        "Mechanics":          ["Kinematics", "Newton's Laws",
                               "Work Energy Power", "Rotational Motion"],
        "Electromagnetism":   ["Electric Fields", "Current & Circuits",
                               "Magnetic Fields"],
        "Modern Physics":     ["Quantum Mechanics", "Nuclear Physics",
                               "Semiconductors"],
    },
    "Biology": {
        "Botany":       ["Plant Physiology", "Plant Reproduction"],
        "Zoology":      ["Human Body Systems", "Genetics"],
        "Microbiology": ["Bacteria & Viruses", "Immunology", "Biotechnology"],
    },
    "General Knowledge": {
        "Current Affairs": ["India", "World Affairs", "Science & Tech"],
        "History":         ["Ancient History", "Modern History",
                            "World History"],
        "Geography":       ["Physical Geography", "Indian Geography",
                            "World Geography"],
        "Civics":          ["Indian Constitution", "Government & Politics"],
    },
    "Aptitude": {
        "Quantitative": ["Number Systems", "Percentages",
                         "Time & Work", "Time Speed Distance"],
        "Logical":      ["Series & Sequences", "Syllogisms",
                         "Puzzles", "Blood Relations"],
        "Verbal":       ["Vocabulary", "Reading Comprehension",
                         "Grammar"],
    },
}


def make_slug(name, parent=None):
    base = f"{parent.slug}-{slugify(name)}" if parent else slugify(name)
    slug = base
    counter = 1
    while Topic.objects.filter(slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def seed():
    created = 0
    for domain_name, subjects in TOPIC_TREE.items():
        domain, _ = Topic.objects.get_or_create(
            name=domain_name,
            parent=None,
            defaults={
                'slug':  make_slug(domain_name),
                'level': 1,
            }
        )
        if _:
            created += 1

        for subject_name, subtopics in subjects.items():
            subject, _ = Topic.objects.get_or_create(
                name=subject_name,
                parent=domain,
                defaults={
                    'slug':  make_slug(subject_name, domain),
                    'level': 2,
                }
            )
            if _:
                created += 1

            for subtopic_name in subtopics:
                subtopic, _ = Topic.objects.get_or_create(
                    name=subtopic_name,
                    parent=subject,
                    defaults={
                        'slug':  make_slug(subtopic_name, subject),
                        'level': 3,
                    }
                )
                if _:
                    created += 1

    print(f"Done — {created} topics created.")


if __name__ == '__main__':
    seed()