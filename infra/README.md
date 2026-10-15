# Infrastructure

Terraform for serving <https://survival-guide.jwall.engineering/> from S3 + CloudFront in the
jwall-engineering AWS account (`650503560686`, `us-east-1`). Applied by CI only, when a
Release Please release PR is merged. Nobody runs `terraform apply` locally.

## What it creates

Two module blocks from the public registry module
[`jwallace145/jwall-engineering/aws`](https://registry.terraform.io/modules/jwallace145/jwall-engineering/aws/latest),
pinned to an exact version in `context.tf` and `main.tf`:

| Module | Creates |
| --- | --- |
| `context` | Nothing. Derives the tag set for the provider's `default_tags` and the bucket name `jwall-engineering-cs-survival-guide`. The `Project` tag is what the apply role's IAM policy keys on. |
| `site` (root module) | ACM certificate, CloudFront distribution, index-rewrite function and Route 53 alias for `survival-guide.jwall.engineering` served from `<bucket>/prod`; a wildcard certificate and distribution for `*.preview.survival-guide.jwall.engineering` served from `<bucket>/previews/pr-<n>`. |

The bucket, the three CI roles and the hosted zone are owned by
[`jwallace145/jwall-engineering-infra`](https://github.com/jwallace145/jwall-engineering-infra),
which registers this site under the project key `cs-survival-guide` in `projects.tf`. This
stack only references them. There is no `dev` environment; the apply role is only allowed to
change the production and preview record names.

| File | Owns |
| --- | --- |
| `versions.tf`, `providers.tf` | Terraform `>= 1.11`, AWS provider `~> 6.0`, region, `default_tags` |
| `backend.tf`, `backend/prod.hcl` | State in `jwall-engineering-tfstate` at `project=cs-survival-guide/env=prod/cs-survival-guide-prod.tfstate`, native lockfile locking |
| `context.tf`, `main.tf` | The two module blocks |
| `variables.tf`, `terraform.tfvars` | `domain_name` and `zone_id`. The zone ID is hardcoded because the CI roles may not list hosted zones. |
| `outputs.tf` | Bucket name and distribution IDs; the deploy workflow reads them with `terraform output -raw` |
| `.terraform.lock.hcl` | Provider checksums for `linux_amd64` (CI) and `darwin_arm64` (local) |
| `.tflint.hcl` | tflint rules, same as the infra repo |

## Bucket layout

| Prefix | Served at | Written by |
| --- | --- | --- |
| `prod/` | `https://survival-guide.jwall.engineering/` | the `deploy` job in `release-please.yml`, with the apply role |
| `previews/pr-<n>/` | `https://pr-<n>.preview.survival-guide.jwall.engineering/` | `preview.yml`, with the preview role; removed when the PR closes, and expired after 14 days by lifecycle rule |

## CI roles

Three IAM roles, created by the infra repo, assumed through GitHub OIDC. No long-lived
keys anywhere.

| Role | Repository variable | Trusted OIDC subject | Used by |
| --- | --- | --- | --- |
| `jwall-engineering-cs-survival-guide-ci-plan` | `AWS_PLAN_ROLE_ARN` | `pull_request` | `terraform plan` job in `build.yml` |
| `jwall-engineering-cs-survival-guide-ci-preview` | `AWS_PREVIEW_ROLE_ARN` | `pull_request` | `preview.yml` |
| `jwall-engineering-cs-survival-guide-ci-apply` | `AWS_APPLY_ROLE_ARN` | `environment:prod` | `deploy` job in `release-please.yml` |

The plan and preview jobs must **not** declare a GitHub environment: that would change
the OIDC subject to `environment:<name>` and the role assumption would fail. The deploy
job must run in the `prod` environment for the same reason.

This repository issues GitHub's immutable OIDC subject
(`repo:jwallace145@35950238/cs-survival-guide@1402607832:...`). The roles trust it only
when the infra repo passes `owner_id` and `repository_id` to its CI role modules
(`ci-plan-role`, `ci-preview-role` and `ci-apply-role`), which its `projects.tf` already
does for this project.

## Workflows

- **Pull requests** (`build.yml`): `build` is the site build and the unit tests.
  `terraform` runs `fmt`, `validate` and `tflint` without credentials and always runs, so
  it can be a required check. `terraform plan` runs only when `infra/` changed, assumes
  the plan role and posts the plan as a comment that is replaced on every push. The plan
  is skipped for fork PRs.
- **Pull requests** (`preview.yml`): builds the site, syncs it to `previews/pr-<n>/` and
  comments the preview URL; deletes the prefix when the PR closes.
- **Release** (`release-please.yml`): when a release PR is merged, the `deploy` job checks
  out the tag, runs `terraform apply`, builds the site with the library version pinned at
  that tag, syncs it to `prod/` with tiered `Cache-Control` (see
  `.github/scripts/sync-site.sh`) and invalidates `/*` on the production distribution.
  `workflow_dispatch` redeploys the latest or a given tag.

Merging to `main` does not deploy. A merged page or `Bump Kit` PR goes live with the next
release PR.

## Local commands

```sh
cd infra
terraform fmt -check -recursive
terraform init -backend=false      # fetches the registry module, no credentials
terraform validate
tflint --init && tflint
```

A real plan needs the plan role or equivalent read-only credentials:
`terraform init -backend-config=backend/prod.hcl && terraform plan`. Never apply locally.

## Upgrading the module

Dependabot's `terraform` ecosystem opens a `chore(deps)` PR when the registry module
publishes a release. The plan comment on that PR shows what the new version changes in
AWS. Read the module's
[CHANGELOG](https://github.com/jwallace145/terraform-aws-jwall-engineering/blob/main/CHANGELOG.md),
check the plan, merge; the change applies with the next release. Keep the two pins
identical.

## Owner hand-off and cutover

One-time steps that need the owner's credentials or the GitHub UI. In order:

1. **Infra repo applied** with `cs-survival-guide` in `projects.tf` (it is registered with
   repository ID `1402607832`). Until the bucket and roles exist every role assumption from
   this repo fails with `Not authorized to perform sts:AssumeRoleWithWebIdentity`.
   Confirm with `terraform output -json projects | jq '.["cs-survival-guide"]'` there.

2. **`prod` environment and repository variables** in this repo:

   ```sh
   export REPO=jwallace145/cs-survival-guide

   gh api -X PUT "repos/$REPO/environments/prod" --input - <<'JSON'
   { "deployment_branch_policy": { "protected_branches": false, "custom_branch_policies": true } }
   JSON
   # The policy applies to the ref the run was triggered from: main for push and
   # workflow_dispatch; release tags are allowed for manual dispatch from a tag.
   gh api -X POST "repos/$REPO/environments/prod/deployment-branch-policies" -f name='main' -f type=branch
   gh api -X POST "repos/$REPO/environments/prod/deployment-branch-policies" -f name='v*' -f type=tag

   gh variable set AWS_PLAN_ROLE_ARN    --repo "$REPO" --body "arn:aws:iam::650503560686:role/jwall-engineering-cs-survival-guide-ci-plan"
   gh variable set AWS_PREVIEW_ROLE_ARN --repo "$REPO" --body "arn:aws:iam::650503560686:role/jwall-engineering-cs-survival-guide-ci-preview"
   gh variable set AWS_APPLY_ROLE_ARN   --repo "$REPO" --body "arn:aws:iam::650503560686:role/jwall-engineering-cs-survival-guide-ci-apply"
   ```

3. **Merge the PR that adds this directory.** Nothing deploys yet; Release Please opens
   a release PR. Previews work from the next pull request onwards.

4. **Check who manages the current DNS record.** `survival-guide.jwall.engineering` is a
   CNAME to GitHub Pages today:

   ```sh
   aws route53 list-resource-record-sets --hosted-zone-id Z029546536VUFGDCPXZ21 \
     --query "ResourceRecordSets[?Name=='survival-guide.jwall.engineering.']"
   ```

   If another Terraform stack manages that record, remove it from that state
   (`terraform state rm ...`) and merge the PR there that drops it, so the two stacks do
   not fight over it.

5. **Merge the release PR.** The deploy job creates the certificates, distributions and
   the preview alias, then **is expected to fail on the `survival-guide.jwall.engineering`
   alias** because Route 53 refuses an A record beside the existing CNAME. State is saved.

6. **Delete the CNAME**:

   ```sh
   aws route53 change-resource-record-sets --hosted-zone-id Z029546536VUFGDCPXZ21 --change-batch '{
     "Changes": [{ "Action": "DELETE", "ResourceRecordSet": {
       "Name": "survival-guide.jwall.engineering", "Type": "CNAME", "TTL": 300,
       "ResourceRecords": [{ "Value": "jwallace145.github.io." }] } }] }'
   ```

   Use the exact values step 4 printed; Route 53 rejects a delete that does not match.

7. **Re-run the Release workflow** with `workflow_dispatch` (no tag: latest release). The
   apply creates the alias, the site syncs, CloudFront is invalidated. Downtime is about
   the CNAME's TTL, because the distribution already exists from step 5.

8. **Afterwards**: disable GitHub Pages (`gh api -X DELETE repos/$REPO/pages`), delete the
   `github-pages` environment and the `gh-pages` branch; add `terraform` to the `main`
   ruleset's required checks; remove `letsencrypt.org` from the CAA list in the infra repo
   once no site is still on GitHub Pages.
