# HTTP Cheat Sheet

Quick reference for the parts of HTTP that come up when designing a service
and are easy to misremember under pressure. It starts with status codes,
because every API in a system design review returns them and the difference
between a `401` and a `403`, or a `502` and a `503`, is the kind of thing an
interviewer asks about. The sheet follows [RFC 9110][rfc9110], the current
HTTP semantics specification.

[rfc9110]: https://www.rfc-editor.org/rfc/rfc9110

## Status codes at a glance

The first digit says who is responsible and what the client should do next.
A client that meets a code it does not know treats it as the `x00` of its
class, so the classes matter more than the long tail of individual codes.

| Class | Meaning | What the client does |
| --- | --- | --- |
| [`1xx`](#1xx-informational) | Informational: the request is in progress | Keeps going; these never end a request |
| [`2xx`](#2xx-success) | Success: the request did what it asked | Uses the response |
| [`3xx`](#3xx-redirection) | Redirection: look somewhere else | Follows `Location`, or uses its cached copy |
| [`4xx`](#4xx-client-error) | Client error: the request was wrong | Fixes the request; retrying as-is will fail again |
| [`5xx`](#5xx-server-error) | Server error: the request may have been fine | Retries later, with backoff |

The codes an API designer actually chooses between are a short list:

| Situation | Code |
| --- | --- |
| Read or update succeeded | `200 OK` |
| Created a resource | `201 Created` plus `Location` |
| Accepted work to do later | `202 Accepted` |
| Succeeded with nothing to return | `204 No Content` |
| Resource unchanged since the client's copy | `304 Not Modified` |
| Malformed request | `400 Bad Request` |
| Who are you? | `401 Unauthorized` |
| I know who you are, and no | `403 Forbidden` |
| No such resource | `404 Not Found` |
| State clash (duplicate, version mismatch) | `409 Conflict` |
| Well-formed but semantically wrong | `422 Unprocessable Content` |
| Over the rate limit | `429 Too Many Requests` plus `Retry-After` |
| We broke | `500 Internal Server Error` |
| We are overloaded or in maintenance | `503 Service Unavailable` plus `Retry-After` |
| An upstream broke or timed out | `502 Bad Gateway` or `504 Gateway Timeout` |

## 1xx Informational

Interim responses. A request can receive several before its final response,
and a client that is not expecting them ignores them.

| Code | Name | When |
| --- | --- | --- |
| `100` | Continue | The client sent `Expect: 100-continue` and may now send the body; lets a server refuse a large upload before it is sent |
| `101` | Switching Protocols | The server accepted an `Upgrade`, most often to WebSocket |
| `103` | Early Hints | Sends `Link` headers so the browser can start fetching assets before the real response is ready |

## 2xx Success

| Code | Name | When |
| --- | --- | --- |
| `200` | OK | The default. The body is the resource (`GET`), the result (`POST`) or the updated resource (`PUT`, `PATCH`) |
| `201` | Created | A new resource exists. `Location` points at it, and the body usually is it |
| `202` | Accepted | The request was valid and queued; the work has not happened yet. Give the client a way to check, such as a job URL in the body |
| `204` | No Content | Success with nothing to say. `DELETE`, and updates where the client does not need the result back |
| `206` | Partial Content | The response is the byte range the client asked for with `Range`. Resumable downloads and video seeking |

**`201` or `200` after `POST`?** `201` when the request made a new resource
with its own URL. `200` when the `POST` was an action (search, calculate,
send) and the body is its result.

**`202` or `200`?** `202` when the response comes back before the work is
done. It is the honest code for anything that goes on a queue.

## 3xx Redirection

The seven redirects differ in two ways: whether the move is permanent, and
whether the client may change the method when it follows the redirect. The
old codes (`301`, `302`) let browsers turn a `POST` into a `GET`; the new
codes (`307`, `308`) do not.

| Code | Name | Permanent | Method kept | When |
| --- | --- | --- | --- | --- |
| `301` | Moved Permanently | yes | no | The old URL is dead for good; caches and search engines update. Safe for `GET` |
| `302` | Found | no | no | Temporary, historically abused. Prefer `303` or `307`, which say which you mean |
| `303` | See Other | no | becomes `GET` | After a `POST`, send the client to `GET` the result: the post-redirect-get pattern that stops a refresh resubmitting a form |
| `304` | Not Modified | n/a | n/a | Not a redirect: the client's cached copy is still good. The answer to a conditional request (`If-None-Match`, `If-Modified-Since`); no body |
| `307` | Temporary Redirect | no | yes | Temporary, and the client repeats the same method and body at the new URL |
| `308` | Permanent Redirect | yes | yes | Permanent, and the client repeats the same method and body. Use for API moves |

Every redirect except `304` carries a `Location` header. Clients follow at
most a handful before giving up, and a loop is a client-side error.

## 4xx Client error

The request is the problem, so retrying it unchanged will produce the same
answer. The response body should say what was wrong; [RFC 9457 problem
details][rfc9457] is the standard shape for it.

[rfc9457]: https://www.rfc-editor.org/rfc/rfc9457

| Code | Name | When |
| --- | --- | --- |
| `400` | Bad Request | The server could not parse the request: bad JSON, a missing required field, a bad parameter type. The catch-all when nothing below fits |
| `401` | Unauthorized | Misnamed: it means *unauthenticated*. No credentials, or bad ones. Must carry `WWW-Authenticate` saying what kind of credentials would do |
| `403` | Forbidden | Authenticated, but not allowed. Retrying with the same credentials will never work. Some APIs return `404` instead, so as not to confirm the resource exists |
| `404` | Not Found | No resource at that URL. Also the polite answer when the client may not know whether it exists |
| `405` | Method Not Allowed | The URL exists but not for this method. Must carry `Allow` listing the methods that work |
| `406` | Not Acceptable | Nothing the server can produce matches the client's `Accept` headers |
| `408` | Request Timeout | The server gave up waiting for the rest of the request. Safe to retry |
| `409` | Conflict | The request clashes with the current state: creating something that exists, updating with a stale version, deleting something in use |
| `410` | Gone | Like `404`, but the resource used to exist and will not come back. Tells clients and crawlers to delete their references |
| `412` | Precondition Failed | A conditional header (`If-Match`, `If-Unmodified-Since`) did not hold. The code behind optimistic concurrency with ETags |
| `413` | Content Too Large | The body exceeds the server's limit. Often with `Retry-After` if the limit is temporary |
| `414` | URI Too Long | Usually a `GET` carrying what should have been a `POST` body |
| `415` | Unsupported Media Type | The server does not understand the request's `Content-Type` |
| `422` | Unprocessable Content | The request parsed but makes no sense: a date in the past, an end before a start. Where `400` is a syntax error, `422` is a semantic one |
| `425` | Too Early | The server will not risk replaying a request sent in TLS early data |
| `426` | Upgrade Required | The client must switch protocols, with `Upgrade` saying which |
| `428` | Precondition Required | The server insists on a conditional header, to force clients to use ETags and avoid lost updates |
| `429` | Too Many Requests | Over the rate limit. Should carry `Retry-After`; the client backs off |
| `431` | Request Header Fields Too Large | Usually a runaway cookie |
| `451` | Unavailable For Legal Reasons | Blocked by a legal demand. The number is the Bradbury reference |

**`401` or `403`?** `401` when the server does not know who is asking.
`403` when it does and the answer is no. Fixing a `401` means logging in;
nothing fixes a `403`.

**`400` or `422`?** `400` when the request could not be read. `422` when it
was read fine and failed validation. Many APIs use `400` for both, which is
allowed; using `422` is a courtesy that separates "fix your client" from
"fix your data".

**`404` or `410`?** `410` only when the resource is known to have been
deleted on purpose and the server wants clients to forget it.

**`409` or `412`?** `412` when the client made its request conditional and
the condition failed. `409` when the clash is in the request itself, with no
precondition involved.

## 5xx Server error

The server failed, or something between the client and the server did. The
request might have been fine, which is why these are the codes a client
retries, with backoff and only for idempotent requests unless it can prove
the first attempt did nothing.

| Code | Name | When |
| --- | --- | --- |
| `500` | Internal Server Error | An unhandled error. The catch-all; the body should not leak the stack trace |
| `501` | Not Implemented | The server does not support the request method at all. Rare; `405` is the per-resource version |
| `502` | Bad Gateway | A proxy or load balancer got an invalid response from the upstream it forwarded to, or could not connect. Means "the thing behind me is broken" |
| `503` | Service Unavailable | The server is up but cannot take the request right now: overloaded, draining, in maintenance. Should carry `Retry-After`. Also what a load balancer returns when no backend is healthy |
| `504` | Gateway Timeout | A proxy or load balancer timed out waiting for the upstream. The request may still be running there |
| `505` | HTTP Version Not Supported | Almost never seen |
| `507` | Insufficient Storage | WebDAV, but the honest code for "disk full" |

**`502`, `503` or `504`?** All three come from the layer in front of a
service. `502` is the backend answering wrongly, `504` is the backend not
answering in time, `503` is nobody available to answer. From the client's
side they are the same instruction: wait, then try again.

**`429` or `503` for shedding load?** `429` when the limit belongs to the
client (its quota). `503` when the limit belongs to the server (its
capacity). Both carry `Retry-After`.

## Retrying

Whether a request can be retried depends on the code and on the method. A
retry is safe when the method is idempotent, meaning repeating it leaves
the server in the same state as doing it once.

| Method | Idempotent | Safe (read-only) |
| --- | --- | --- |
| `GET`, `HEAD`, `OPTIONS` | yes | yes |
| `PUT`, `DELETE` | yes | no |
| `POST`, `PATCH` | no | no |

| Code | Retry? |
| --- | --- |
| `408`, `425`, `429`, `502`, `503`, `504` | Yes, after `Retry-After` or with exponential backoff and jitter |
| `500` | Maybe, once, for idempotent requests only |
| Any other `4xx` | No; the same request gets the same answer |
| `2xx`, `3xx` | Not a retry: use the response or follow the redirect |

A `POST` can be made retryable by giving each attempt an idempotency key,
so the server recognises a repeat and returns the first attempt's response
instead of acting twice.
