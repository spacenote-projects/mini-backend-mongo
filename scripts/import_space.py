#!/usr/bin/env python3
"""
Import space data from JSON file using the SpaceNote API.

This script imports a complete space including:
- Users (creates if they don't exist)
- Space with fields
- Space members
- Notes with custom fields
- Comments on notes
"""

import argparse
import json
import sys
from typing import Any

import httpx


class SpaceImporter:
    """Import space data from JSON using HTTP API."""

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self.session = httpx.Client(headers=self.headers)

    def _request(
        self, method: str, endpoint: str, json_data: dict[str, Any] | None = None
    ) -> httpx.Response:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, json=json_data)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            print(f"ERROR: Request failed for {method} {endpoint}: {e}")
            try:
                error_detail = e.response.json()
                print(f"Error details: {json.dumps(error_detail, indent=2)}")
            except Exception:
                print(f"Response text: {e.response.text}")
            raise
        except httpx.HTTPError as e:
            print(f"ERROR: Request failed for {method} {endpoint}: {e}")
            raise

    def get_existing_users(self) -> set[str]:
        """Get list of existing usernames."""
        response = self._request("GET", "/users")
        users = response.json()
        return {user["username"] for user in users}

    def create_user(self, username: str, token: str) -> None:
        """Create a new user."""
        data = {"username": username, "token": token}
        self._request("POST", "/users", data)
        print(f" Created user: {username}")

    def create_space(self, slug: str, title: str) -> None:
        """Create a new space."""
        data = {"slug": slug, "title": title}
        self._request("POST", "/spaces", data)
        print(f" Created space: {slug} ({title})")

    def add_space_field(self, space_slug: str, field: dict[str, Any]) -> None:
        """Add a custom field to the space."""
        self._request("POST", f"/spaces/{space_slug}/fields", field)
        print(f"   Added field: {field['id']} ({field['type']})")

    def add_space_member(self, space_slug: str, username: str) -> None:
        """Add a member to the space."""
        data = {"username": username}
        self._request("POST", f"/spaces/{space_slug}/members", data)
        print(f"   Added member: {username}")

    def create_note(self, space_slug: str, fields: dict[str, Any]) -> int:
        """Create a note and return its number."""
        # Convert tags from list to comma-separated string
        if "tags" in fields and isinstance(fields["tags"], list):
            fields["tags"] = ", ".join(fields["tags"])

        data = {"fields": fields}
        response = self._request("POST", f"/spaces/{space_slug}/notes", data)
        note = response.json()
        return note["number"]

    def create_comment(
        self, space_slug: str, note_number: int, content: str
    ) -> None:
        """Create a comment on a note."""
        data = {"content": content}
        self._request(
            "POST", f"/spaces/{space_slug}/notes/{note_number}/comments", data
        )

    def import_data(self, data: dict[str, Any]) -> None:
        """Import complete space data from JSON structure."""
        space_data = data["space"]
        notes_data = data["notes"]
        comments_data = data["comments"]

        # Step 1: Collect all unique usernames
        print("\n[1/6] Collecting usernames...")
        usernames = set(space_data["members"])
        usernames.update(note["author_username"] for note in notes_data)
        usernames.update(comment["author_username"] for comment in comments_data)
        print(f"Found {len(usernames)} unique users: {', '.join(sorted(usernames))}")

        # Step 2: Create users if they don't exist
        print("\n[2/6] Creating users...")
        existing_users = self.get_existing_users()
        for username in sorted(usernames):
            if username in existing_users:
                print(f"  - User already exists: {username}")
            else:
                # Use username as token for simplicity
                self.create_user(username, username)

        # Step 3: Create space
        print("\n[3/6] Creating space...")
        self.create_space(space_data["slug"], space_data["title"])

        # Step 4: Add fields to space
        print("\n[4/6] Adding custom fields...")
        for field in space_data["fields"]:
            self.add_space_field(space_data["slug"], field)

        # Step 5: Add members to space
        print("\n[5/6] Adding members to space...")
        for member in space_data["members"]:
            self.add_space_member(space_data["slug"], member)

        # Step 6: Create notes
        print(f"\n[6/6] Importing {len(notes_data)} notes...")
        note_number_map = {}  # Map original number to new number
        for i, note in enumerate(notes_data, 1):
            original_number = note["number"]
            new_number = self.create_note(space_data["slug"], note["fields"])
            note_number_map[original_number] = new_number
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(notes_data)} notes created...")

        print(f" Created {len(notes_data)} notes")

        # Step 7: Create comments
        print(f"\n[7/7] Importing {len(comments_data)} comments...")
        comments_by_note = {}
        for comment in comments_data:
            original_note_number = comment["note_number"]
            if original_note_number not in comments_by_note:
                comments_by_note[original_note_number] = []
            comments_by_note[original_note_number].append(comment)

        total_comments = 0
        for original_note_number, comments in comments_by_note.items():
            new_note_number = note_number_map[original_note_number]
            for comment in comments:
                self.create_comment(
                    space_data["slug"], new_note_number, comment["content"]
                )
                total_comments += 1

        print(f" Created {total_comments} comments")
        print(f"\n Import completed successfully!")
        print(
            f"   Space '{space_data['slug']}' with {len(notes_data)} notes and {total_comments} comments"
        )


def main() -> None:
    """Parse arguments and run import."""
    parser = argparse.ArgumentParser(
        description="Import space data from JSON file to SpaceNote backend"
    )
    parser.add_argument(
        "--token",
        default="admin",
        help="Admin authentication token (default: admin)",
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to JSON file containing space data",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:3100/api/v1",
        help="Base URL of the API (default: http://localhost:3100/api/v1)",
    )

    args = parser.parse_args()

    # Load JSON data
    try:
        with open(args.file, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in file {args.file}: {e}")
        sys.exit(1)

    # Validate JSON structure
    required_keys = ["space", "notes", "comments"]
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        print(f"ERROR: Missing required keys in JSON: {', '.join(missing_keys)}")
        sys.exit(1)

    # Run import
    importer = SpaceImporter(args.base_url, args.token)
    try:
        importer.import_data(data)
    except Exception as e:
        print(f"\nL Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
