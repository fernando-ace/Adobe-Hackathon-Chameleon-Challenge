# Offline Docker validation

Revalidated 2026-10-15 with Docker Desktop engine 29.5.3.

Build for the challenge architecture:

```powershell
docker build --platform linux/amd64 -t chameleon-engine .
```

The build succeeded. `Dockerfile` leaves platform selection to the command-line flag, avoiding Docker's redundant `FROM --platform` warning.

Offline run:

```powershell
docker run --rm --network none `
  -v "${PWD}/input:/app/input" `
  -v "${PWD}/evidence/docker:/app/output" `
  chameleon-engine
```

All three official samples completed with `OK`, and the repository validator reported zero issues for every output:

- Level 1: 0.13 s; PNG 110,453 bytes
- Level 2: 0.17 s; PNG 72,511 bytes
- Level 3: 0.26 s; PNG 41,146 bytes

The generated JSON retained source element IDs and counts, text content, and font families. Output geometry stayed within each target canvas. Contain-fit images retained their source frame ratios; cover-fit backgrounds use a target-sized frame by design. The only warning on the offline run was Fontconfig's non-fatal `05-reset-dirs-sample.conf` warning.

To recover Docker Desktop after an unclean shutdown, this host had orphaned Windows socket reparse points in both `%LOCALAPPDATA%\Docker\run` and `%LOCALAPPDATA%\docker-secrets-engine`. Direct socket deletion failed with Windows error 1920. Renaming the socket-only runtime directories aside let Docker recreate them; Docker then answered `docker info` and ran the offline image. The preserved directories are outside the repository.
