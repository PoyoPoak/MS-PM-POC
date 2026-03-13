const DEFAULT_REPOSITORY_URL = "https://github.com/PoyoPoak/MS-PM-POC"

function parseGithubRepository(
  url: string,
): { owner: string; repo: string } | null {
  const match = url.match(/github\.com[/:]([^/]+)\/([^/.]+)(?:\.git)?$/i)
  if (!match) {
    return null
  }

  return { owner: match[1], repo: match[2] }
}

export async function getLatestCommitHash(
  repositoryUrl = import.meta.env.VITE_REPOSITORY_URL ?? DEFAULT_REPOSITORY_URL,
): Promise<string | null> {
  const repository = parseGithubRepository(repositoryUrl)
  if (!repository) {
    return null
  }

  try {
    const response = await fetch(
      `https://api.github.com/repos/${repository.owner}/${repository.repo}/commits?per_page=1`,
      {
        headers: {
          Accept: "application/vnd.github+json",
        },
      },
    )

    if (!response.ok) {
      return null
    }

    const payload = (await response.json()) as Array<{ sha?: string }>
    return payload[0]?.sha?.slice(0, 7) ?? null
  } catch {
    return null
  }
}
