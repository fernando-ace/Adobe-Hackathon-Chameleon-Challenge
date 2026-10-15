# Offline Docker validation

Validated 2026-10-15 with Docker Desktop engine 29.5.3.

Build:

```powershell
docker build --platform linux/amd64 -t chameleon-engine .
```

Offline run:

```powershell
docker run --rm --network none `
  -v "${PWD}/input:/app/input" `
  -v "${PWD}/evidence/docker:/app/output" `
  chameleon-engine
```

All three official tasks completed with `OK` and rendered PNGs:

- Level 1: 0.21 s
- Level 2: 0.17 s
- Level 3: 0.18 s

The generated JSON retained each source element ID and count, text content, and font family. Output geometry stayed within each target canvas. Contain-fit images retained their source frame ratios; cover-fit backgrounds use a target-sized frame by design. PNG previews were produced for every level. Docker emitted a non-fatal Fontconfig warning about the distribution's `05-reset-dirs-sample.conf` and its exporter warns that the Dockerfile pins `FROM --platform=linux/amd64` while the build also selects that platform.

To recover Docker Desktop after an unclean shutdown, this host had orphaned Windows socket reparse points in both `%LOCALAPPDATA%\Docker\run` and `%LOCALAPPDATA%\docker-secrets-engine`. Direct socket deletion failed with Windows error 1920. Renaming the socket-only runtime directories aside let Docker recreate them; Docker then answered `docker info` and ran the offline image. The preserved directories are outside the repository.
