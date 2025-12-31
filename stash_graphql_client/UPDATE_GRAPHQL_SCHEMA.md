# Updating Stash GraphQL Schema

The GraphQL schema files in `schema/` are reference documentation from the upstream Stash project.

## Update Process

```bash
# If stash-upstream remote doesn't exist yet, add it:
git remote add stash-upstream https://github.com/stashapp/stash.git

# Fetch latest upstream
git fetch stash-upstream develop

# Switch to a new branch, so you can push this up to GH and pass the linting protection on main
git checkout -b chore/schema_update

# Remove old schema
git rm -r stash_graphql_client/schema/

# Add updated schema
git read-tree --prefix=stash_graphql_client/schema/ -u stash-upstream/develop:graphql/schema

# Commit the update
git commit -m "chore: update Stash GraphQL schema from upstream"

#Push the branch to GH, wait for the linting protection to pass, then merge and cleanup
git push -u origin chore/schema_update
git checkout main && git fetch && git pull && git merge --ff-only chore/schema_update
git push && git push origin --delete chore/schema_update && git branch -d chore/schema_update
```

## Note

The actual GraphQL queries used by this project are in `fragments.py`, not these `.graphql` files. The schema files serve as API reference documentation only.
