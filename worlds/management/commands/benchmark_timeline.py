import math
import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext

from worlds.models import Character, CharacterWorldEntry, Post, World


BENCHMARK_USER_EMAIL = "benchmark_timeline@example.com"
BENCHMARK_USER_HANDLE = "benchmark_timeline"
BENCHMARK_WORLD_TITLE = "__timeline_benchmark_world__"
BENCHMARK_CHARACTER_NAME = "Benchmark Character"


class Command(BaseCommand):
    help = "Measure timeline response time, query count, and error rate for SLO checks."

    def add_arguments(self, parser):
        parser.add_argument("--post-count", type=int, default=200, help="Minimum posts to prepare.")
        parser.add_argument("--runs", type=int, default=20, help="Number of requests for each scenario.")

    def handle(self, *args, **options):
        post_count = max(50, int(options["post_count"]))
        runs = max(5, int(options["runs"]))

        world = self._prepare_data(post_count)
        first_page_url = f"/worlds/{world.id}/timeline/"
        next_cursor = self._get_next_cursor(world)

        first_page_result = self._measure(first_page_url, runs)
        cursor_page_result = self._measure(f"{first_page_url}?cursor={next_cursor}", runs)

        self.stdout.write("[timeline benchmark]")
        self.stdout.write(
            f"dataset_posts={post_count} runs={runs} world_id={world.id}"
        )
        self.stdout.write("scenario, p95_ms, avg_ms, max_ms, avg_queries, max_queries, error_rate")
        self.stdout.write(self._format_result("first_page", first_page_result))
        self.stdout.write(self._format_result("cursor_page", cursor_page_result))

    def _prepare_data(self, post_count):
        user_model = get_user_model()
        owner, _ = user_model.objects.get_or_create(
            email=BENCHMARK_USER_EMAIL,
            defaults={
                "username": "benchmark_timeline_user",
                "handle": BENCHMARK_USER_HANDLE,
                "display_name": "Timeline Benchmark",
            },
        )
        if not owner.handle:
            owner.handle = BENCHMARK_USER_HANDLE
            owner.save(update_fields=["handle"])

        world, _ = World.objects.get_or_create(
            title=BENCHMARK_WORLD_TITLE,
            owner=owner,
            defaults={"visibility": World.Visibility.PUBLIC},
        )
        if world.visibility != World.Visibility.PUBLIC:
            world.visibility = World.Visibility.PUBLIC
            world.save(update_fields=["visibility"])

        character, _ = Character.objects.get_or_create(
            world=world,
            name=BENCHMARK_CHARACTER_NAME,
            defaults={"owner": owner},
        )
        if character.owner_id != owner.id:
            character.owner = owner
            character.save(update_fields=["owner"])

        CharacterWorldEntry.objects.get_or_create(
            character=character,
            world=world,
            defaults={"added_by": owner},
        )

        current_count = Post.objects.filter(world=world).count()
        missing = max(0, post_count - current_count)
        if missing:
            posts = [
                Post(world=world, character=character, author=owner, text=f"benchmark post {index}")
                for index in range(missing)
            ]
            Post.objects.bulk_create(posts)

        return world

    def _get_next_cursor(self, world):
        posts = list(
            Post.objects.filter(world=world)
            .order_by("-created_at", "-id")[:20]
        )
        if not posts:
            raise RuntimeError("Benchmark world has no posts.")
        pivot = posts[-1]
        return f"{pivot.created_at.isoformat()}|{pivot.id}"

    def _measure(self, url, runs):
        client = Client(HTTP_HOST="localhost")
        elapsed_ms = []
        query_counts = []
        errors = 0

        for _ in range(runs):
            start = time.perf_counter()
            with CaptureQueriesContext(connection) as captured:
                response = client.get(url)
            duration = (time.perf_counter() - start) * 1000
            elapsed_ms.append(duration)
            query_counts.append(len(captured))
            if response.status_code != 200:
                errors += 1

        elapsed_sorted = sorted(elapsed_ms)
        p95_index = max(0, math.ceil(0.95 * len(elapsed_sorted)) - 1)

        return {
            "p95_ms": elapsed_sorted[p95_index],
            "avg_ms": sum(elapsed_ms) / len(elapsed_ms),
            "max_ms": max(elapsed_ms),
            "avg_queries": sum(query_counts) / len(query_counts),
            "max_queries": max(query_counts),
            "error_rate": errors / runs,
        }

    def _format_result(self, scenario, result):
        return (
            f"{scenario}, "
            f"{result['p95_ms']:.2f}, "
            f"{result['avg_ms']:.2f}, "
            f"{result['max_ms']:.2f}, "
            f"{result['avg_queries']:.2f}, "
            f"{result['max_queries']}, "
            f"{result['error_rate']:.2%}"
        )
