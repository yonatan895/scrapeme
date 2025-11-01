# Docker (fast builds)

- Uses a multi-stage Dockerfile with uv to prebuild wheels and install from cache.
- BuildKit/buildx caching pushes/pulls cache via GHCR to speed up CI and local builds.

## Local builds

- Standard production image (BuildKit on):

```bash
DOCKER_BUILDKIT=1 docker build -t scrapeme:latest --target production .
```

- Buildx with GHCR cache (faster on cold machines):

```bash
docker buildx build \
  --target production \
  --cache-from type=registry,ref=ghcr.io/yonatan895/scrapeme:buildcache \
  --cache-to type=registry,ref=ghcr.io/yonatan895/scrapeme:buildcache,mode=max \
  -t ghcr.io/yonatan895/scrapeme:latest \
  .
```

- Development image:

```bash
docker buildx build --target dev .
```

- Test image:

```bash
docker buildx build --target test .
```

## CI (GitHub Actions)

- Workflow `.github/workflows/docker-build.yml` sets up buildx, logs into GHCR, and builds:
  - Production image (pushed with tags: latest on default branch, plus SHA)
  - Dev image (not pushed) to warm cache layers
  - Shares cache under `ghcr.io/yonatan895/scrapeme:buildcache`

## Notes

- The Dockerfile copies lock files (requirements*.txt, pyproject.toml) before source code to maximize cache hits for dependency layers.
- Wheels are built once in `deps-builder` and installed into production, avoiding recompilation.
- `.dockerignore` aggressively excludes venvs, caches, artifacts, git metadata, and build outputs to keep context small.
