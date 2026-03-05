"""Hashnode GraphQL API cross-posting."""

from myworkflow.shared.http import create_client


HASHNODE_API = "https://gql.hashnode.com"

PUBLISH_MUTATION = """
mutation PublishPost($input: PublishPostInput!) {
  publishPost(input: $input) {
    post {
      id
      url
      slug
    }
  }
}
"""


def publish_article(
    api_key: str,
    publication_id: str,
    title: str,
    body_markdown: str,
    tags: list[str],
    canonical_url: str,
) -> dict:
    """Publish an article on Hashnode."""
    client = create_client(
        base_url=HASHNODE_API,
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json",
        },
    )

    tag_objects = [{"slug": t.lower().replace(" ", "-"), "name": t} for t in tags[:5]]

    variables = {
        "input": {
            "title": title,
            "contentMarkdown": body_markdown,
            "publicationId": publication_id,
            "tags": tag_objects,
            "originalArticleURL": canonical_url,
        }
    }

    resp = client.post(
        "/",
        json={"query": PUBLISH_MUTATION, "variables": variables},
    )
    resp.raise_for_status()
    data = resp.json()

    post_data = data["data"]["publishPost"]["post"]
    return {
        "id": post_data["id"],
        "url": post_data["url"],
        "slug": post_data["slug"],
    }
