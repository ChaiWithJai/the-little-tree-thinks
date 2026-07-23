# Bonsai state routing

The URL is the public state boundary for the workbench. Each durable or recoverable state has one canonical route.

| Route | Authority | Recovery behavior |
| --- | --- | --- |
| `/` | Ephemeral UI state | Opens a clean Day 0 surface. |
| `/draft/:id` | Browser `localStorage` | Restores the prompt, selected capability, corpus, page type, and any image result on the same browser profile. The 20 most recent drafts are retained. |
| `/jobs/:id` | Server job store | Reconnects to an active job. A completed job is replaced in browser history by its canonical `/runs/:id` URL. |
| `/runs/:id` | Server run store | Restores a retained result and its review/continuation surface from any browser that can reach this server. |

The history transitions mirror the user's mental model:

1. Entering the first meaningful prompt creates and pushes a draft URL.
2. Starting the work pushes the job URL.
3. Completing the work replaces the transient job URL with the retained run URL.
4. Back and forward navigation reapply the corresponding state rather than leaving stale UI in memory.

## Cache contracts

| Resource | Policy |
| --- | --- |
| HTML shell, JavaScript, CSS | `no-cache` with an ETag, so navigation revalidates without redownloading unchanged bytes. |
| Case and page-preset catalogs | Private 60-second cache with five-minute stale-while-revalidate and an ETag. |
| Status, jobs, runs, and other dynamic API responses | `no-store`, so workflow state is never served stale. |
| Generated image and preview artifacts | Private one-year immutable cache because their URLs identify fixed artifacts. |

Draft URLs are intentionally local and private. Jobs and retained runs are server-addressable. This separation keeps half-written work on the device while making accepted work reliably recoverable.
