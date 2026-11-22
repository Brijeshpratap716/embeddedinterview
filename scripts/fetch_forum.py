#!/usr/bin/env python3
"""Fetch GitHub Discussions into content/forum.json for the static forum.

Runs inside GitHub Actions with GITHUB_TOKEN (needs `discussions: read`).
Never fails the build: on any error it leaves a valid (possibly empty) file.
"""
import json, os, sys, urllib.request

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "content", "forum.json")
REPO = os.environ.get("GITHUB_REPOSITORY", "Brijeshpratap716/embeddedinterview")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

AUTHOR = "author { login avatarUrl url }"
QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    hasDiscussionsEnabled
    discussionCategories(first: 25) { nodes { name slug emoji description } }
    discussions(first: 50, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title url createdAt upvoteCount body bodyHTML locked isAnswered
        category { name slug }
        %s
        labels(first: 10) { nodes { name } }
        comments(first: 60) {
          totalCount
          nodes {
            %s createdAt bodyHTML upvoteCount isAnswer
            replies(first: 30) { nodes { %s createdAt bodyHTML } }
          }
        }
      }
    }
  }
}""" % (AUTHOR, AUTHOR, AUTHOR)


def gql(variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": "embeddedinterview-forum"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]["repository"]


def main():
    result = {"enabled": False, "categories": [], "discussions": []}
    try:
        if not TOKEN:
            raise RuntimeError("GITHUB_TOKEN not set")
        owner, name = REPO.split("/")
        cursor = None
        for _ in range(10):                       # up to 500 discussions
            repo = gql({"owner": owner, "name": name, "cursor": cursor})
            result["enabled"] = bool(repo["hasDiscussionsEnabled"])
            result["categories"] = repo["discussionCategories"]["nodes"]
            d = repo["discussions"]
            result["discussions"] += d["nodes"]
            if not d["pageInfo"]["hasNextPage"]:
                break
            cursor = d["pageInfo"]["endCursor"]
        print(f"forum: {len(result['discussions'])} discussions")
    except Exception as e:                          # keep the site building
        print(f"forum: fetch skipped ({e})", file=sys.stderr)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
