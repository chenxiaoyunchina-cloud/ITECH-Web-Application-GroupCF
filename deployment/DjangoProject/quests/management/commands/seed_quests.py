import random
from django.core.management.base import BaseCommand
from quests.models import QuestTemplate


class Command(BaseCommand):
    help = "Seed QuestTemplate with lots of quest cards (default 120)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=120, help="How many quest cards to create (default 120).")
        parser.add_argument(
            "--refresh",
            action="store_true",
            help="Delete all existing QuestTemplates before seeding (dangerous).",
        )

    def handle(self, *args, **options):
        count = options["count"]
        refresh = options["refresh"]

        if count <= 0:
            self.stdout.write(self.style.ERROR("--count must be > 0"))
            return

        if refresh:
            deleted, _ = QuestTemplate.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Refresh enabled: deleted {deleted} existing quest templates."))

        #deterministic seed so our set stays stable across runs
        random.seed(42)

        #pickers
        def pick(seq):
            return random.choice(seq)

        #core phrases
        guaranteed = [
            {
                "name": "Colour Hunt",
                "description": "Find 5 different colours in the city. Take a photo of each.",
                "type": "WALK",
                "group_limits": "1-6",
                "duration": 45,
            },
            {
                "name": "This Bench Is Nice",
                "description": "Find a bench with a view. Sit for 2 minutes. Write one line about the vibe.",
                "type": "WALK",
                "group_limits": "1-4",
                "duration": 15,
            },
            {
                "name": "I Can Sit Here",
                "description": "Pick a spot you would genuinely sit at again. Snap a picture and save the location.",
                "type": "WALK",
                "group_limits": "1-4",
                "duration": 15,
            },
            {
                "name": "Skyline Sniper",
                "description": "Capture the best skyline shot you can. Bonus if you get a reflection.",
                "type": "WALK",
                "group_limits": "1-6",
                "duration": 40,
            },
        ]

        #pattern storage
        photo_targets = [
            "street sign", "mural", "doorway", "window", "bridge", "bike rack", "statue",
            "weird poster", "neon sign", "cat", "plant", "coffee cup", "library corner",
            "staircase", "graffiti tag", "bus stop", "market stall", "book cover",
        ]
        vibe_prompts = [
            "quiet corner", "chaotic corner", "unexpected calm", "main character moment",
            "rainy mood", "sunny mood", "late-night vibe", "morning vibe", "windy vibe",
        ]
        mini_actions = [
            "write one sentence", "take one photo", "record 10 seconds of ambient sound",
            "count to 30", "send a friend a picture", "sketch for 60 seconds",
        ]
        navigation = [
            "follow the river", "walk toward the tallest building you can see",
            "take 3 left turns in a row", "follow a tram line for 2 stops",
            "walk until you find a park", "walk until you find a café you have never tried",
            "walk to the nearest library", "walk to a place with live noticeboards",
        ]
        socials = [
            "ask someone for a local recommendation", "compliment a stranger’s outfit",
            "thank a worker you interact with", "leave a kind note somewhere appropriate",
        ]
        transit_tasks = [
            "ride 2 stops and explore the area", "take a bus to a random stop and walk back",
            "use a different route home than usual", "get off one stop early and explore",
        ]
        cycle_tasks = [
            "find the smoothest road", "find the worst cobblestone",
            "cycle to a viewpoint", "cycle a loop you have never done",
            "find a new bike-friendly shortcut",
        ]
        sensory = [
            "best smell", "best sound", "best texture", "best light",
            "best reflection", "best shadow", "best colour",
        ]
        micro_titles = [
            "Vibe Check", "Tiny Discovery", "Small Win", "Soft Reset", "Blink Quest",
            "Pocket Adventure", "Mood Booster", "Side Alley Special",
        ]
        group_limits_by_style = [
            "1-1", "1-2", "1-4", "1-6", "2-6", "4-10"
        ]

        def mk_quest(name, desc, qtype):
            #picking group limits and duration based on type and vibes lol
            if qtype == "CYCLE":
                duration = pick([25, 30, 35, 40, 45, 60, 75])
                group_limits = pick(["1-1", "1-2", "1-4", "1-6"])
            elif qtype == "TRANSIT":
                duration = pick([20, 25, 30, 35, 40, 45, 60])
                group_limits = pick(["1-1", "1-2", "1-4", "1-6"])
            elif qtype == "WALK":
                duration = pick([10, 15, 20, 25, 30, 35, 40, 45, 60, 75, 90])
                group_limits = pick(group_limits_by_style)
            else:  #mixed
                duration = pick([20, 30, 40, 45, 60, 75, 90, 120])
                group_limits = pick(group_limits_by_style)

            return {
                "name": name[:120],
                "description": desc,
                "type": qtype,
                "group_limits": group_limits,
                "duration": duration,
            }

        generated = []
        used_names = set(q["name"].strip().lower() for q in guaranteed)

        #building a big pool of unique quests
        while len(generated) + len(guaranteed) < count:
            qtype = pick(["WALK", "WALK", "WALK", "MIXED", "CYCLE", "TRANSIT"])  # bias toward WALK

            if qtype == "WALK":
                style = pick(["photo", "vibe", "nav", "sensory", "micro", "social"])
                if style == "photo":
                    target = pick(photo_targets)
                    name = f"{target.title()} Safari"
                    desc = f"Find 3 different {target}s. Take a photo of each and rank them 1 to 3."
                elif style == "vibe":
                    vibe = pick(vibe_prompts)
                    name = f"{vibe.title()} Scan"
                    desc = f"Find a {vibe}. {pick(mini_actions)} to capture it."
                elif style == "nav":
                    rule = pick(navigation)
                    name = f"Rule Walk: {rule[:28].title()}"
                    desc = f"Do this rule: {rule}. Stop when you find something interesting and document it."
                elif style == "sensory":
                    s = pick(sensory)
                    name = f"{s.title()} Hunter"
                    desc = f"Find the {s} you can. Capture it with a photo and one sentence."
                elif style == "social":
                    s = pick(socials)
                    name = "Tiny Social Quest"
                    desc = f"{s}. Then write one sentence about how it felt."
                else:
                    tag = pick(micro_titles)
                    name = f"{tag}: {pick(vibe_prompts).title()}"
                    desc = f"Walk 5 minutes. Find one detail you have never noticed. {pick(mini_actions)}."

            elif qtype == "CYCLE":
                task = pick(cycle_tasks)
                name = f"Cycle Quest: {task.title()[:35]}"
                desc = f"{task}. Take one photo at the end point and one on the way back."

            elif qtype == "TRANSIT":
                task = pick(transit_tasks)
                name = f"Transit Quest: {task.title()[:35]}"
                desc = f"{task}. When you get off, find one spot worth pinning."

            else:  #mixede
                target = pick(photo_targets)
                vibe = pick(vibe_prompts)
                name = f"Mixed Mission: {target.title()} + {vibe.title()}"
                desc = f"Use any way to move. Find a {target} that matches a {vibe}. Take a photo and write a short caption."

            key = name.strip().lower()
            if key in used_names:
                #we make it unique by adding a tiny suffix
                name = f"{name} #{random.randint(2, 999)}"
                key = name.strip().lower()
                if key in used_names:
                    continue

            used_names.add(key)
            generated.append(mk_quest(name, desc, qtype))

        all_quests = guaranteed + generated

        created = 0
        skipped = 0

        for q in all_quests:
            if QuestTemplate.objects.filter(name=q["name"]).exists():
                skipped += 1
                continue

            QuestTemplate.objects.create(
                name=q["name"],
                description=q["description"],
                type=q["type"],
                group_limits=q["group_limits"],
                duration=q["duration"],
                is_active=True,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete. Created {created} quest cards. Skipped {skipped} duplicates."
        ))